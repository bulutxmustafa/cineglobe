"""Social services (plan §3.11, Faz 7C)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone

from apps.accounts.models import Notification
from apps.catalog.tmdb_client import TMDBClient, TMDBError, TMDBNotFoundError
from apps.notebook.models import NotebookEntry
from apps.search.cost_guard import local_today
from apps.search.models import DailyCounter
from apps.social.models import (
    Block,
    NotebookShare,
    Profile,
    Report,
    UserList,
    UserListItem,
    Visibility,
)
from apps.social.text import clean_text, contains_banned_word, username_problem

logger = logging.getLogger(__name__)

USERNAME_CHANGE_INTERVAL = timedelta(days=30)
COMMUNITY_MIN_VOTES = 5
AUTO_HIDE_REPORTS = 3
REPORTER_MIN_ACCOUNT_AGE = timedelta(hours=24)
DAILY_LIST_CREATIONS = 20
DAILY_REPORTS = 20


class SocialError(Exception):
    """A rule was broken; `code` is stable for API responses."""

    def __init__(self, code: str, field: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.field = field


def checked_text(value: str, field: str) -> str:
    text = clean_text(value)
    if contains_banned_word(text):
        raise SocialError("banned_word", field)
    return text


# --- Profile -------------------------------------------------------------------


def update_profile(user, data: dict[str, Any]) -> Profile:
    profile = Profile.objects.filter(user=user).first()
    username = data.get("username")
    if profile is None and not username:
        raise SocialError("username_required", "username")
    if username is not None:
        username = username.strip().lower()
        if problem := username_problem(username):
            raise SocialError(problem, "username")
        if profile is None or username != profile.username:
            taken = (
                Profile.objects.filter(username=username).exclude(user=user).exists()
            )
            if taken:
                raise SocialError("username_taken", "username")
            if (
                profile is not None
                and profile.username_changed_at
                and timezone.now() - profile.username_changed_at
                < USERNAME_CHANGE_INTERVAL
            ):
                raise SocialError("username_change_too_soon", "username")
    if profile is None:
        profile = Profile(user=user, username=username)
    elif username and username != profile.username:
        profile.username = username
        profile.username_changed_at = timezone.now()
    for field in ("display_name", "bio"):
        if field in data:
            setattr(profile, field, checked_text(data[field], field))
    for field in (
        "avatar_kind",
        "avatar_poster_path",
        "profile_visibility",
        "show_stats",
    ):
        if field in data:
            setattr(profile, field, data[field])
    profile.full_clean()
    profile.save()
    return profile


# --- Lists -------------------------------------------------------------------------


def _limit(user, key: str, per_day: int) -> None:
    if not DailyCounter.add_if_below(f"social:{key}:{user.pk}", local_today(), per_day):
        raise SocialError("daily_limit")


def create_list(user, data: dict[str, Any]) -> UserList:
    if UserList.objects.filter(owner=user).count() >= UserList.MAX_PER_USER:
        raise SocialError("too_many_lists")
    _limit(user, "list_create", DAILY_LIST_CREATIONS)
    return UserList.objects.create(
        owner=user,
        slug=secrets.token_urlsafe(9)[:12],
        title=checked_text(data["title"], "title"),
        description=checked_text(data.get("description", ""), "description"),
        is_ranked=data.get("is_ranked", True),
        visibility=data.get("visibility", Visibility.PRIVATE),
    )


def update_list(user_list: UserList, data: dict[str, Any]) -> UserList:
    for field in ("title", "description"):
        if field in data:
            setattr(user_list, field, checked_text(data[field], field))
    for field in ("is_ranked", "visibility"):
        if field in data:
            setattr(user_list, field, data[field])
    user_list.save()
    return user_list


def _item_snapshot(
    client: TMDBClient, media_type: str, tmdb_id: int, language: str
) -> dict:
    if media_type == "movie":
        data = client.get_movie_detail(tmdb_id, language=language)
        released = data.get("release_date") or ""
    else:
        data = client.get_tv_detail(tmdb_id, language=language)
        released = data.get("first_air_date") or ""
    return {
        "title": (data.get("title") or data.get("name") or "")[:255],
        "poster_path": data.get("poster_path") or "",
        "year": int(released[:4]) if released[:4].isdigit() else None,
        "snapshot_at": timezone.now(),
    }


def replace_items(
    user_list: UserList, items: list[dict], client: TMDBClient | None, language: str
) -> list[UserListItem]:
    """Set the full ordered item list in one transaction (no half-sorted list).

    Existing titles keep their TMDB snapshot; only new ones are fetched.
    """
    if len(items) > UserList.MAX_ITEMS:
        raise SocialError("too_many_items")
    keys = [(i["media_type"], i["tmdb_id"]) for i in items]
    if len(set(keys)) != len(keys):
        raise SocialError("duplicate_item")
    existing = {(i.media_type, i.tmdb_id): i for i in user_list.items.all()}
    snapshots: dict[tuple[str, int], dict] = {}
    for key in keys:
        if key in existing:
            continue
        if client is None:
            raise TMDBError("TMDB client required")
        try:
            snapshots[key] = _item_snapshot(client, key[0], key[1], language)
        except TMDBNotFoundError:
            raise SocialError("title_not_found") from None
    with transaction.atomic():
        user_list.items.all().delete()
        created = []
        for position, item in enumerate(items, start=1):
            key = (item["media_type"], item["tmdb_id"])
            old = existing.get(key)
            snapshot = snapshots.get(key) or {
                "title": old.title,
                "poster_path": old.poster_path,
                "year": old.year,
                "snapshot_at": old.snapshot_at,
            }
            created.append(
                UserListItem(
                    user_list=user_list,
                    media_type=key[0],
                    tmdb_id=key[1],
                    position=position,
                    comment=checked_text(item.get("comment", ""), "comment")[:280],
                    **snapshot,
                )
            )
        UserListItem.objects.bulk_create(created)
        user_list.save(update_fields=["updated_at"])
    return created


def clone_list(user_list: UserList, user) -> UserList:
    copy = create_list(
        user,
        {
            "title": user_list.title,
            "description": user_list.description,
            "is_ranked": user_list.is_ranked,
        },
    )
    UserListItem.objects.bulk_create(
        UserListItem(
            user_list=copy,
            media_type=i.media_type,
            tmdb_id=i.tmdb_id,
            position=i.position,
            title=i.title,
            poster_path=i.poster_path,
            year=i.year,
            snapshot_at=i.snapshot_at,
        )
        for i in user_list.items.all()
    )
    return copy


# --- Notebook sharing --------------------------------------------------------------


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_share(
    user,
    scope: str = "ratings",
    statuses: list[str] | None = None,
    expires_in_days: int | None = None,
) -> tuple[NotebookShare, str]:
    token = secrets.token_urlsafe(24)  # 192 bits; returned once, only the hash is kept
    share = NotebookShare.objects.create(
        user=user,
        token_hash=_hash(token),
        scope=scope,
        statuses=statuses or [],
        expires_at=(
            timezone.now() + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        ),
    )
    return share, token


def resolve_share(token: str) -> NotebookShare | None:
    if not token or len(token) > 64:
        return None
    digest = _hash(token)
    share = (
        NotebookShare.objects.filter(token_hash=digest).select_related("user").first()
    )
    if share is None or not hmac.compare_digest(share.token_hash, digest):
        return None
    if share.revoked_at or (share.expires_at and share.expires_at <= timezone.now()):
        return None
    if not share.user.is_active:
        return None
    return share


def shared_entries(share: NotebookShare) -> list[dict[str, Any]]:
    entries = NotebookEntry.objects.filter(user=share.user, status__isnull=False)
    if share.statuses:
        entries = entries.filter(status__in=share.statuses)
    rows = []
    for entry in entries:
        row = {
            "media_type": entry.media_type,
            "tmdb_id": entry.tmdb_id,
            "title": entry.title,
            "year": entry.year,
            "poster_path": entry.poster_path,
            "status": entry.status,
            "rating_x2": entry.rating_x2,
            "is_favorite": entry.is_favorite,
        }
        # Notes only when the owner chose so AND did not lock this note.
        if share.scope == NotebookShare.Scope.RATINGS_NOTES and not entry.note_locked:
            row["note"] = entry.note
        rows.append(row)
    return rows


# --- Community -------------------------------------------------------------------------


@dataclass(frozen=True)
class CommunityRating:
    average: float | None
    votes: int | None


def community_rating(media_type: str, tmdb_id: int) -> CommunityRating:
    """Anonymous average of every member's rating (private ones included), shown only
    from COMMUNITY_MIN_VOTES votes so a single person's rating is never exposed."""
    agg = NotebookEntry.objects.filter(
        media_type=media_type,
        tmdb_id=tmdb_id,
        rating_x2__isnull=False,
        user__is_active=True,
    ).aggregate(avg=Avg("rating_x2"), n=Count("id"))
    if (agg["n"] or 0) < COMMUNITY_MIN_VOTES:
        return CommunityRating(None, None)
    return CommunityRating(round(agg["avg"] / 2, 2), agg["n"])


# --- Moderation --------------------------------------------------------------------------


def report(
    reporter, target_type: str, target_id: int, reason: str, details: str
) -> tuple[Report, bool]:
    """Record a report; returns (report, newly_hidden). Repeats by the same user count once."""
    target = _target(target_type, target_id)
    if target is None or _target_owner_id(target) == reporter.pk:
        raise SocialError("invalid_target")
    _limit(reporter, "report", DAILY_REPORTS)
    counts = timezone.now() - reporter.date_joined >= REPORTER_MIN_ACCOUNT_AGE
    item, created = Report.objects.get_or_create(
        reporter=reporter,
        target_type=target_type,
        target_id=target_id,
        defaults={
            "reason": reason,
            "details": clean_text(details)[:200],
            "counts": counts,
        },
    )
    if not created:
        return item, False
    distinct = (
        Report.objects.filter(
            target_type=target_type,
            target_id=target_id,
            counts=True,
            resolved_at__isnull=True,
        )
        .values("reporter")
        .distinct()
        .count()
    )
    if distinct >= AUTO_HIDE_REPORTS and not target.is_hidden:
        target.is_hidden = True
        target.save(update_fields=["is_hidden"])
        _notify_hidden(target)
        return item, True
    return item, False


def _target(target_type: str, target_id: int):
    model = {"profile": Profile, "list": UserList}.get(target_type)
    return model.objects.filter(pk=target_id).first() if model else None


def _target_owner_id(target) -> int:
    return target.user_id if isinstance(target, Profile) else target.owner_id


def _notify_hidden(target) -> None:
    owner = target.user if isinstance(target, Profile) else target.owner
    language = (
        owner.preferred_language if owner.preferred_language in ("tr", "en") else "tr"
    )
    what = {
        "tr": "profilin" if isinstance(target, Profile) else "listen",
        "en": "profile" if isinstance(target, Profile) else "list",
    }[language]
    message = {
        "tr": f"Şikâyetler nedeniyle {what} geçici olarak gizlendi. İtiraz için destek adresimize yazabilirsin.",
        "en": f"Your {what} was hidden after several reports. Contact support to appeal.",
    }[language]
    Notification.objects.create(
        user=owner, kind=Notification.Kind.CONTENT_HIDDEN, message=message[:300]
    )


def block(blocker, username: str) -> Block:
    target = (
        Profile.objects.filter(username=username.strip().lower())
        .select_related("user")
        .first()
    )
    if target is None or target.user_id == blocker.pk:
        raise SocialError("invalid_target")
    item, _ = Block.objects.get_or_create(blocker=blocker, blocked=target.user)
    return item


def unblock(blocker, username: str) -> None:
    Block.objects.filter(
        blocker=blocker, blocked__profile__username=username.strip().lower()
    ).delete()


# --- Export (KVKK/GDPR) -----------------------------------------------------------------


def export_social(user) -> dict[str, Any]:
    profile = Profile.objects.filter(user=user).first()
    return {
        "profile": (
            {
                "username": profile.username,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "profile_visibility": profile.profile_visibility,
                "show_stats": profile.show_stats,
            }
            if profile
            else None
        ),
        "lists": [
            {
                "title": lst.title,
                "description": lst.description,
                "visibility": lst.visibility,
                "items": [
                    {
                        "media_type": i.media_type,
                        "tmdb_id": i.tmdb_id,
                        "position": i.position,
                        "comment": i.comment,
                    }
                    for i in lst.items.all()
                ],
            }
            for lst in UserList.objects.filter(owner=user).prefetch_related("items")
        ],
        "shares": [
            {
                "scope": s.scope,
                "statuses": s.statuses,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
                "view_count": s.view_count,
            }
            for s in NotebookShare.objects.filter(user=user)
        ],
        "blocks": list(
            Block.objects.filter(blocker=user).values_list(
                "blocked__profile__username", flat=True
            )
        ),
    }
