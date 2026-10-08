"""Upcoming movies and series (plan §3.7, Faz 4C).

Facts this relies on (checked against live TMDB data on 2026-10-08):
- discover/movie with `region=TR` + `release_date.gte` returns the *Turkish*
  release date in `release_date` (e.g. a film out 16 Dec globally shows 18 Dec);
  films without a Turkish date come from a global `primary_release_date` query.
- "Returning series" queries are topped by talk shows; Talk/News/Reality genres
  are excluded and a new season counts only when `next_episode_to_air` is
  episode 1 of a season.
- TMDB does not say how precise a date is: a full date is reported as "day",
  a missing one as "unknown".

"Today" is the Europe/Istanbul date, so a title released today stays listed
today and drops off at local midnight.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache

from apps.catalog.formatting import format_tmdb_item
from apps.catalog.genre_map import genre_ids_for
from apps.catalog.tmdb_client import TMDBClient, TMDBError

logger = logging.getLogger(__name__)

Group = Literal["this_week", "this_month", "later", "tba"]
GROUP_ORDER: tuple[str, ...] = ("this_week", "this_month", "later", "tba")
NOISE_TV_GENRES = "10767,10763,10764"  # Talk, News, Reality
PAGE_SIZE = 20
SOURCE_PAGES = 2  # TMDB pages per source (20 titles each)
RETURNING_LOOKAHEAD_DAYS = 90
RETURNING_DETAIL_LIMIT = 20
MAX_WORKERS = 8


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.QUOTA_TIME_ZONE)).date()


def group_for(release: str, today: date) -> Group:
    """Bucket an ISO date relative to `today` (assumed not in the past)."""
    if not release:
        return "tba"
    day = date.fromisoformat(release)
    if day <= today + timedelta(days=6):
        return "this_week"
    if (day.year, day.month) == (today.year, today.month):
        return "this_month"
    return "later"


class UpcomingService:
    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def page(
        self,
        *,
        media_type: str,
        language: str,
        page: int,
        genre: str | None = None,
        month: str | None = None,
    ) -> dict[str, Any]:
        today = local_today()
        items = self.items(language, today)
        if media_type in ("movie", "tv"):
            items = [i for i in items if i["media_type"] == media_type]
        if genre:
            items = [i for i in items if self._has_genre(i, genre)]
        if month:
            items = [i for i in items if i["release_date"].startswith(month)]

        total = len(items)
        total_pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
        start = (page - 1) * PAGE_SIZE
        results = items[start : start + PAGE_SIZE]
        return {
            "today": today.isoformat(),
            "media_type": media_type,
            "page": page,
            "total_pages": total_pages,
            "total_results": total,
            "results": results,
            "groups": [
                {"key": key, "items": [r for r in results if r["group"] == key]}
                for key in GROUP_ORDER
                if any(r["group"] == key for r in results)
            ],
        }

    def items(self, language: str, today: date) -> list[dict[str, Any]]:
        """Every upcoming title, sorted by date (undated last). Cached per local day."""
        key = f"upcoming:v1:{settings.UPCOMING_REGION}:{language}:{today.isoformat()}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = self._collect(language, today)
        cache.set(key, result, settings.UPCOMING_CACHE_TTL_SECONDS)
        return result

    # ------------------------------------------------------------------

    def _collect(self, language: str, today: date) -> list[dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}

        def add(
            raw: dict[str, Any], media_type: str, release: str, region: str, **extra
        ):
            if raw.get("adult"):
                return
            # A Turkish theatrical date already signals relevance; global sources
            # carry a long tail of titles almost nobody has heard of.
            if (
                region != settings.UPCOMING_REGION
                and (raw.get("popularity") or 0) < settings.UPCOMING_MIN_POPULARITY
            ):
                return
            item = format_tmdb_item(raw, default_media_type=media_type)
            if release and release < today.isoformat():
                return  # already out (e.g. stale cached data): never list the past
            key = f"{media_type}:{item['tmdb_id']}"
            if key in found:  # the first source wins (Turkish date before global)
                return
            item.update(
                release_date=release,
                date_precision="day" if release else "unknown",
                region=region if release else "",
                group=group_for(release, today),
                **extra,
            )
            found[key] = item

        region = settings.UPCOMING_REGION
        for raw in self._pages(
            self._client.discover_movies,
            {
                "region": region,
                "release_date.gte": today.isoformat(),
                "with_release_type": "2|3",
                "sort_by": "popularity.desc",
            },
            language,
        ):
            add(raw, "movie", raw.get("release_date") or "", region)

        for raw in self._pages(
            self._client.discover_movies,
            {
                "primary_release_date.gte": today.isoformat(),
                "sort_by": "popularity.desc",
            },
            language,
        ):
            add(raw, "movie", raw.get("release_date") or "", "global")

        for raw in self._pages(
            self._client.discover_tv,
            {
                "first_air_date.gte": today.isoformat(),
                "without_genres": NOISE_TV_GENRES,
                "sort_by": "popularity.desc",
            },
            language,
        ):
            add(raw, "tv", raw.get("first_air_date") or "", "global", season_number=1)

        for raw, next_episode in self._returning_seasons(language, today):
            add(
                raw,
                "tv",
                next_episode["air_date"],
                "global",
                season_number=next_episode.get("season_number"),
            )

        return sorted(
            found.values(),
            key=lambda i: (
                not i["release_date"],
                i["release_date"],
                -(i["popularity"] or 0),
            ),
        )

    def _pages(
        self, discover, params: dict[str, Any], language: str
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for page in range(1, SOURCE_PAGES + 1):
            data = discover({**params, "page": page}, language=language)
            results.extend(data.get("results", []))
            if page >= (data.get("total_pages") or 1):
                break
        return results

    def _returning_seasons(self, language: str, today: date):
        """(series, next_episode) for series whose next season starts soon."""
        window_end = today + timedelta(days=RETURNING_LOOKAHEAD_DAYS)
        airing = self._client.discover_tv(
            {
                "air_date.gte": today.isoformat(),
                "air_date.lte": window_end.isoformat(),
                "with_status": "0",  # Returning Series
                "without_genres": NOISE_TV_GENRES,
                "sort_by": "popularity.desc",
                "page": 1,
            },
            language=language,
        ).get("results", [])[:RETURNING_DETAIL_LIMIT]

        def next_episode(raw):
            try:
                detail = self._client.get_tv_detail(raw["id"], language=language)
            except TMDBError as exc:
                logger.warning("Skipping series %s: %s", raw.get("id"), exc)
                return raw, None
            return raw, detail.get("next_episode_to_air")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            pairs = list(pool.map(next_episode, airing))
        return [
            (raw, nxt)
            for raw, nxt in pairs
            if nxt
            and nxt.get("episode_number") == 1
            and (nxt.get("air_date") or "") >= today.isoformat()
        ]

    @staticmethod
    def _has_genre(item: dict[str, Any], genre: str) -> bool:
        wanted = set(genre_ids_for([genre], item["media_type"])[0])
        return bool(wanted & set(item.get("genre_ids") or []))
