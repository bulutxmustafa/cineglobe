"""Retriever: SearchFilters → candidate titles from TMDB discover.

Movie and TV use different genre IDs (see genre_map), so each media type gets
its own discover query; for media_type="both" the two run in parallel. Keyword
and person names are resolved to TMDB IDs first. When keyword matching is too
narrow, the query is retried without keywords so the user still gets results.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from apps.catalog.formatting import format_tmdb_item
from apps.catalog.genre_map import get_movie_genre_ids, get_tv_genre_ids
from apps.catalog.tmdb_client import TMDBClient
from apps.search.schemas import SearchFilters

logger = logging.getLogger(__name__)

# Discover pre-filter: drop obscure titles early; the ranker applies confidence.
MIN_VOTES_DISCOVER = {"movie": 150, "tv": 50}
# Retry without keywords when fewer results than this come back.
MIN_RESULTS_BEFORE_RELAX = 5
# TMDB with_status: 0 Returning Series, 3 Ended, 4 Canceled.
TV_STATUS = {"ongoing": "0", "ended": "3|4"}


def _without_adult(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Belt and braces: include_adult=false is also sent on every discover call.
    return [r for r in results if not r.get("adult")]


def _ids(values: list[int]) -> str:
    return ",".join(str(v) for v in dict.fromkeys(values))


class Retriever:
    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def fetch(self, filters: SearchFilters, language: str) -> list[dict[str, Any]]:
        """Return formatted candidates; each carries media_type and matched_keywords."""
        keyword_ids = self._resolve_keywords(filters.keywords)
        person_ids = self._resolve_people(filters.people)

        media_types = (
            ["movie", "tv"] if filters.media_type == "both" else [filters.media_type]
        )
        if person_ids and filters.media_type == "both":
            # discover/tv cannot filter by person; unfiltered TV would be noise.
            media_types = ["movie"]
        if len(media_types) == 1:
            return self._fetch_one(
                media_types[0], filters, keyword_ids, person_ids, language
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    self._fetch_one, mt, filters, keyword_ids, person_ids, language
                )
                for mt in media_types
            ]
            # .result() re-raises TMDB errors so the view can map them to 503.
            return [item for future in futures for item in future.result()]

    # ------------------------------------------------------------------

    def _fetch_one(
        self,
        media_type: str,
        filters: SearchFilters,
        keyword_ids: list[int],
        person_ids: list[int],
        language: str,
    ) -> list[dict[str, Any]]:
        params = self.build_params(media_type, filters, keyword_ids, person_ids)
        discover = (
            self._client.discover_movies
            if media_type == "movie"
            else self._client.discover_tv
        )
        results = _without_adult(discover(params, language=language).get("results", []))
        matched_keywords = bool(keyword_ids)

        if keyword_ids and len(results) < MIN_RESULTS_BEFORE_RELAX:
            relaxed = self.build_params(media_type, filters, [], person_ids)
            extra = _without_adult(
                discover(relaxed, language=language).get("results", [])
            )
            seen = {r.get("id") for r in results}
            tagged = [dict(r, _kw=True) for r in results]
            tagged += [dict(r, _kw=False) for r in extra if r.get("id") not in seen]
            return [self._format(r, media_type, r.pop("_kw")) for r in tagged]

        return [self._format(r, media_type, matched_keywords) for r in results]

    @staticmethod
    def _format(item: dict[str, Any], media_type: str, matched: bool) -> dict[str, Any]:
        formatted = format_tmdb_item(item, default_media_type=media_type)
        formatted["matched_keywords"] = matched
        return formatted

    @staticmethod
    def build_params(
        media_type: str,
        filters: SearchFilters,
        keyword_ids: list[int],
        person_ids: list[int],
    ) -> dict[str, Any]:
        """Translate filters into TMDB discover parameters for one media type."""
        to_ids = get_movie_genre_ids if media_type == "movie" else get_tv_genre_ids
        params: dict[str, Any] = {
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "vote_count.gte": MIN_VOTES_DISCOVER[media_type],
        }
        if include := to_ids(filters.genres_include):
            # Comma = AND for up to two genres; more than that would be too narrow.
            sep = "," if len(set(include)) <= 2 else "|"
            params["with_genres"] = sep.join(str(g) for g in dict.fromkeys(include))
        if exclude := to_ids(filters.genres_exclude):
            params["without_genres"] = _ids(exclude)
        if keyword_ids:
            params["with_keywords"] = "|".join(str(k) for k in keyword_ids)
        if filters.min_rating is not None:
            params["vote_average.gte"] = filters.min_rating

        date_field = (
            "primary_release_date" if media_type == "movie" else "first_air_date"
        )
        if filters.year_from:
            params[f"{date_field}.gte"] = f"{filters.year_from}-01-01"
        if filters.year_to:
            params[f"{date_field}.lte"] = f"{filters.year_to}-12-31"

        if media_type == "movie":
            if person_ids:
                params["with_people"] = _ids(person_ids)
            if filters.runtime_max:
                params["with_runtime.lte"] = filters.runtime_max
        else:
            # TMDB discover/tv has no with_people; people are a movie-side filter here.
            if filters.episode_runtime_max:
                params["with_runtime.lte"] = filters.episode_runtime_max
            if filters.status in TV_STATUS:
                params["with_status"] = TV_STATUS[filters.status]
        return params

    def _resolve_keywords(self, keywords: list[str]) -> list[int]:
        ids: list[int] = []
        for keyword in keywords:
            results = self._client.search_keyword(keyword).get("results", [])
            exact = [r for r in results if r.get("name", "").lower() == keyword]
            match = exact or results[:1]
            if match:
                ids.append(match[0]["id"])
        return list(dict.fromkeys(ids))

    def _resolve_people(self, people: list[str]) -> list[int]:
        ids: list[int] = []
        for name in people:
            results = self._client.search_person(name).get("results", [])
            if results:
                ids.append(results[0]["id"])
        return ids
