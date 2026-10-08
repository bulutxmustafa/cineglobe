"""Reminder service layer (plan §3.7, Faz 4C). Sending notifications arrives in Faz 7.

Release dates come from TMDB and follow the same rules as the upcoming list:
the Turkish theatrical date for movies when one exists (global otherwise), and
for series either the premiere or the first episode of the next season.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.catalog.tmdb_client import TMDBClient, TMDBError, TMDBNotFoundError
from apps.reminders.models import Reminder
from apps.upcoming.service import local_today

logger = logging.getLogger(__name__)

# TMDB release types: 2 = theatrical (limited), 3 = theatrical.
THEATRICAL_TYPES = {2, 3}


class ReminderError(Exception):
    """A reminder cannot be created; `code` is stable for API error responses."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ReleaseInfo:
    title: str
    release_date: date | None
    season_number: int | None = None


def _parse(value: str | None) -> date | None:
    try:
        return date.fromisoformat((value or "")[:10]) if value else None
    except ValueError:
        return None


def movie_release(client: TMDBClient, tmdb_id: int, language: str) -> ReleaseInfo:
    detail = client.get_movie_detail(tmdb_id, language=language)
    release = _parse(detail.get("release_date"))
    region = settings.UPCOMING_REGION
    for country in client.get_movie_release_dates(tmdb_id).get("results", []):
        if country.get("iso_3166_1") != region:
            continue
        dates = sorted(
            parsed
            for entry in country.get("release_dates", [])
            if entry.get("type") in THEATRICAL_TYPES
            and (parsed := _parse(entry.get("release_date")))
        )
        if dates:
            release = dates[0]
    return ReleaseInfo(detail.get("title") or "", release)


def tv_release(
    client: TMDBClient, tmdb_id: int, language: str, today: date
) -> ReleaseInfo:
    detail = client.get_tv_detail(tmdb_id, language=language)
    title = detail.get("name") or ""
    premiere = _parse(detail.get("first_air_date"))
    if premiere is None or premiere >= today:
        return ReleaseInfo(title, premiere, 1)
    upcoming = detail.get("next_episode_to_air") or {}
    if upcoming.get("episode_number") == 1:
        return ReleaseInfo(
            title, _parse(upcoming.get("air_date")), upcoming.get("season_number")
        )
    # Running mid-season or no announced season: nothing to remind about.
    return ReleaseInfo(title, None)


def release_info(
    client: TMDBClient, media_type: str, tmdb_id: int, language: str
) -> ReleaseInfo:
    if media_type == "movie":
        return movie_release(client, tmdb_id, language)
    return tv_release(client, tmdb_id, language, local_today())


def create_reminder(
    user,
    *,
    media_type: str,
    tmdb_id: int,
    remind_on: str = Reminder.RemindOn.RELEASE_DAY,
    channels: list[str] | None = None,
    language: str = "tr",
    client: TMDBClient,
) -> tuple[Reminder, bool]:
    """Create (or reactivate/update) the user's reminder for a title.

    Returns (reminder, created). One reminder per user and title: asking again
    updates the existing one instead of creating a duplicate.
    """
    try:
        info = release_info(client, media_type, tmdb_id, language)
    except TMDBNotFoundError:
        raise ReminderError("title_not_found") from None
    today = local_today()
    if info.release_date is not None and info.release_date < today:
        raise ReminderError("already_released")
    if media_type == "tv" and info.release_date is None and info.season_number is None:
        raise ReminderError("no_upcoming_season")

    values: dict[str, Any] = {
        "title": info.title[:200],
        "season_number": info.season_number,
        "remind_on": remind_on,
        "channels": channels or ["in_app"],
        "status": Reminder.Status.PENDING,
        "last_known_release_date": info.release_date,
        "sent_at": None,
    }
    with transaction.atomic():
        reminder, created = Reminder.objects.select_for_update().get_or_create(
            user=user, media_type=media_type, tmdb_id=tmdb_id, defaults=values
        )
        if not created:
            for field, value in values.items():
                setattr(reminder, field, value)
        reminder.full_clean()
        reminder.save()
    return reminder, created


def cancel_reminder(reminder: Reminder) -> Reminder:
    if reminder.status != Reminder.Status.CANCELLED:
        reminder.status = Reminder.Status.CANCELLED
        reminder.save(update_fields=["status", "updated_at"])
    return reminder


def refresh_release_dates(
    reminders, client: TMDBClient, language: str = "tr"
) -> list[Reminder]:
    """Re-read release dates for pending reminders; return the ones that moved.

    Used by the daily job (Faz 7) so users hear about postponed releases.
    TMDB failures skip that reminder and keep its last known date.
    """
    changed: list[Reminder] = []
    for reminder in reminders:
        if reminder.status != Reminder.Status.PENDING:
            continue
        try:
            info = release_info(client, reminder.media_type, reminder.tmdb_id, language)
        except TMDBError as exc:
            logger.warning("Could not refresh reminder %s: %s", reminder.pk, exc)
            continue
        if info.release_date != reminder.last_known_release_date:
            reminder.last_known_release_date = info.release_date
            reminder.release_date_changed_at = timezone.now()
            reminder.save(
                update_fields=[
                    "last_known_release_date",
                    "release_date_changed_at",
                    "updated_at",
                ]
            )
            changed.append(reminder)
    return changed


def due_reminders(today: date | None = None):
    """Pending reminders whose notification day has come (sending: Faz 7)."""
    today = today or local_today()
    pending = Reminder.objects.filter(
        status=Reminder.Status.PENDING, last_known_release_date__isnull=False
    ).select_related("user")
    return [r for r in pending if r.due_date() is not None and r.due_date() <= today]
