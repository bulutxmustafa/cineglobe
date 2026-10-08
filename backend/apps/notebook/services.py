"""Film Notebook services (plan §3.8, Faz 7B)."""

from __future__ import annotations

import csv
import io
import logging
from collections import Counter
from datetime import timedelta
from typing import Any

from django.db.models import F, Q, QuerySet
from django.utils import timezone

from apps.catalog.genre_map import genre_name_from_movie_id, genre_name_from_tv_id
from apps.catalog.tmdb_client import TMDBClient, TMDBError, TMDBNotFoundError
from apps.notebook.models import NotebookEntry

logger = logging.getLogger(__name__)

SNAPSHOT_REFRESH_AFTER = timedelta(days=30)
SNAPSHOT_MAX_AGE = timedelta(days=182)  # TMDB terms: at most 6 months
SNAPSHOT_FIELDS = (
    "title",
    "original_title",
    "poster_path",
    "year",
    "genres",
    "runtime_minutes",
    "episode_runtime",
    "episode_count",
    "snapshot_at",
)
LOOKUP_LIMIT = 100


def fetch_snapshot(
    client: TMDBClient, media_type: str, tmdb_id: int, language: str
) -> dict[str, Any]:
    """Public TMDB data kept on the entry. Raises TMDBNotFoundError for unknown titles."""
    if media_type == "movie":
        data = client.get_movie_detail(tmdb_id, language=language)
        lookup = genre_name_from_movie_id
        released = data.get("release_date") or ""
        snapshot = {"runtime_minutes": data.get("runtime") or None}
    else:
        data = client.get_tv_detail(tmdb_id, language=language)
        lookup = genre_name_from_tv_id
        released = data.get("first_air_date") or ""
        # TMDB now leaves `episode_run_time` empty (checked 2026-10-09); fall back to
        # the last aired episode's runtime.
        runtimes = data.get("episode_run_time") or []
        last = data.get("last_episode_to_air") or {}
        snapshot = {
            "episode_runtime": (runtimes[0] if runtimes else last.get("runtime"))
            or None,
            "episode_count": data.get("number_of_episodes") or None,
        }
    genres = [lookup(g.get("id")) for g in data.get("genres", [])]
    return {
        **snapshot,
        "title": (data.get("title") or data.get("name") or "")[:255],
        "original_title": (
            data.get("original_title") or data.get("original_name") or ""
        )[:255],
        "poster_path": data.get("poster_path") or "",
        "year": int(released[:4]) if released[:4].isdigit() else None,
        "genres": [g for g in genres if g],
        "snapshot_at": timezone.now(),
    }


def upsert_entry(
    user,
    media_type: str,
    tmdb_id: int,
    changes: dict[str, Any],
    *,
    client: TMDBClient | None,
    language: str = "tr",
) -> tuple[NotebookEntry, bool]:
    """Create or update the user's entry. A new entry gets a TMDB snapshot first."""
    entry = NotebookEntry.objects.filter(
        user=user, media_type=media_type, tmdb_id=tmdb_id
    ).first()
    created = entry is None
    if created:
        if client is None:
            raise TMDBError("TMDB client required to create an entry")
        snapshot = fetch_snapshot(client, media_type, tmdb_id, language)  # 404 → caller
        entry = NotebookEntry(
            user=user, media_type=media_type, tmdb_id=tmdb_id, **snapshot
        )
    for field, value in changes.items():
        setattr(entry, field, value)
    if (
        entry.status == NotebookEntry.Status.WATCHED
        and entry.watched_on is None
        and "watched_on" not in changes
    ):
        entry.watched_on = timezone.localdate()
    entry.full_clean()
    entry.save()
    return entry, created


def lookup(user, keys: list[tuple[str, int]]) -> dict[str, dict[str, Any]]:
    """Notebook state for many titles in one query (result cards: "Watched ✓ · 4½★")."""
    if not keys:
        return {}
    ids = {tmdb_id for _, tmdb_id in keys}
    wanted = {f"{m}:{i}" for m, i in keys}
    rows = NotebookEntry.objects.filter(user=user, tmdb_id__in=ids).values(
        "media_type", "tmdb_id", "status", "is_favorite", "rating_x2"
    )
    result = {}
    for row in rows:
        key = f"{row['media_type']}:{row['tmdb_id']}"
        if key in wanted:  # same id as the other media type is not a match
            result[key] = {
                "status": row["status"],
                "is_favorite": row["is_favorite"],
                "rating_x2": row["rating_x2"],
            }
    return result


def watched_keys(user) -> set[str]:
    """Titles the user marked watched ("hide what I've watched" filter)."""
    if not user or not user.is_authenticated:
        return set()
    rows = NotebookEntry.objects.filter(
        user=user, status=NotebookEntry.Status.WATCHED
    ).values_list("media_type", "tmdb_id")
    return {f"{m}:{i}" for m, i in rows}


def merge_guest_favorites(
    user, items: list[tuple[str, int]], client: TMDBClient | None, language: str
) -> dict[str, int]:
    """Bring browser-only favourites into the account after sign-in.

    Existing entries are left as they are (account data wins on conflict); only
    missing titles are created as favourites.
    """
    existing = {
        f"{m}:{i}"
        for m, i in NotebookEntry.objects.filter(user=user).values_list(
            "media_type", "tmdb_id"
        )
    }
    added = skipped = 0
    for media_type, tmdb_id in dict.fromkeys(items):
        if f"{media_type}:{tmdb_id}" in existing:
            skipped += 1
            continue
        try:
            upsert_entry(
                user,
                media_type,
                tmdb_id,
                {"is_favorite": True},
                client=client,
                language=language,
            )
            added += 1
        except (TMDBError, TMDBNotFoundError) as exc:
            logger.warning("Favourite %s:%s not merged: %s", media_type, tmdb_id, exc)
            skipped += 1
    return {"added": added, "skipped": skipped}


def stats(user) -> dict[str, Any]:
    """Notebook statistics from a single query over the user's entries."""
    entries = list(
        NotebookEntry.objects.filter(user=user).only(
            "media_type",
            "status",
            "rating_x2",
            "genres",
            "watched_on",
            "updated_at",
            "runtime_minutes",
            "episode_runtime",
            "episode_count",
            "rewatch_count",
            "title",
            "tmdb_id",
            "poster_path",
            "year",
        )
    )
    watched = [e for e in entries if e.status == NotebookEntry.Status.WATCHED]
    rated = [e for e in entries if e.rating_x2]
    distribution = Counter(e.rating_x2 for e in rated)
    genres = Counter(g for e in watched for g in e.genres)
    by_month = Counter(
        (e.watched_on or e.updated_at.date()).strftime("%Y-%m") for e in watched
    )
    by_year = Counter((e.watched_on or e.updated_at.date()).year for e in watched)
    top = sorted(rated, key=lambda e: (e.rating_x2, e.updated_at), reverse=True)[:10]
    return {
        "watched_movies": sum(1 for e in watched if e.media_type == "movie"),
        "watched_series": sum(1 for e in watched if e.media_type == "tv"),
        "want_to_watch": sum(
            1 for e in entries if e.status == NotebookEntry.Status.WANT_TO_WATCH
        ),
        "favorites": sum(1 for e in entries if e.is_favorite),
        "total_watch_minutes": sum(e.watch_minutes() for e in watched),
        "average_rating": (
            round(sum(e.rating_x2 for e in rated) / len(rated) / 2, 2)
            if rated
            else None
        ),
        "rating_distribution": {str(k): distribution.get(k, 0) for k in range(1, 11)},
        "genre_distribution": dict(genres.most_common()),
        "watched_by_month": dict(sorted(by_month.items())),
        "watched_by_year": {str(k): v for k, v in sorted(by_year.items())},
        "top_rated": [
            {
                "media_type": e.media_type,
                "tmdb_id": e.tmdb_id,
                "title": e.title,
                "year": e.year,
                "poster_path": e.poster_path,
                "rating_x2": e.rating_x2,
            }
            for e in top
        ],
    }


EXPORT_COLUMNS = [
    "media_type",
    "tmdb_id",
    "title",
    "year",
    "status",
    "is_favorite",
    "rating",
    "note",
    "tags",
    "watched_on",
    "rewatch_count",
    "progress_season",
    "progress_episode",
]


def export_rows(user) -> list[dict[str, Any]]:
    return [
        {
            "media_type": e.media_type,
            "tmdb_id": e.tmdb_id,
            "title": e.title,
            "year": e.year,
            "status": e.status or "",
            "is_favorite": e.is_favorite,
            "rating": e.rating_x2 / 2 if e.rating_x2 else None,
            "note": e.note,
            "tags": e.tags,
            "watched_on": e.watched_on.isoformat() if e.watched_on else None,
            "rewatch_count": e.rewatch_count,
            "progress_season": e.progress_season,
            "progress_episode": e.progress_episode,
        }
        for e in NotebookEntry.objects.filter(user=user)
    ]


def export_csv(user) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for row in export_rows(user):
        writer.writerow({**row, "tags": "|".join(row["tags"])})
    return buffer.getvalue()


def refresh_snapshots(
    client: TMDBClient | None, batch: int = 100, language: str = "tr"
) -> dict[str, int]:
    """Daily job part: refresh old snapshots; past 6 months clear TMDB fields instead."""
    now = timezone.now()
    # Never-filled or cleared snapshots (NULL) are retried too, oldest first.
    stale: QuerySet = NotebookEntry.objects.filter(
        Q(snapshot_at__lt=now - SNAPSHOT_REFRESH_AFTER) | Q(snapshot_at__isnull=True)
    ).order_by(F("snapshot_at").asc(nulls_first=True))[:batch]
    refreshed = cleared = 0
    for entry in stale:
        try:
            if client is None:
                raise TMDBError("no TMDB client")
            for field, value in fetch_snapshot(
                client, entry.media_type, entry.tmdb_id, language
            ).items():
                setattr(entry, field, value)
            entry.save(update_fields=[*SNAPSHOT_FIELDS])
            refreshed += 1
        except TMDBError as exc:
            if entry.snapshot_at and entry.snapshot_at < now - SNAPSHOT_MAX_AGE:
                # Keep the user's status, rating and note; drop all TMDB-sourced data.
                NotebookEntry.objects.filter(pk=entry.pk).update(
                    title="",
                    original_title="",
                    year=None,
                    poster_path="",
                    genres=[],
                    runtime_minutes=None,
                    episode_runtime=None,
                    episode_count=None,
                    snapshot_at=None,
                )
                cleared += 1
            else:
                logger.warning("Snapshot refresh failed for %s: %s", entry.pk, exc)
    return {"refreshed": refreshed, "cleared": cleared}
