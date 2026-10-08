"""RecipeEngine: Collection recipe → TMDB discover → ranked, cached title list (plan §3.5).

The generated list is cached per (collection, media type, language) and the
cache key contains a digest of the editable fields, so an edit in the admin is
visible on the next request without any manual cache clearing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from typing import Any

from django.conf import settings
from django.core.cache import cache

from apps.catalog.formatting import format_tmdb_item
from apps.catalog.genre_map import genre_ids_for
from apps.catalog.tmdb_client import TMDBClient, TMDBNotFoundError
from apps.collections.models import Collection
from apps.collections.recipe import Recipe
from apps.search.ranker import bayesian_rating

logger = logging.getLogger(__name__)

MAX_ITEMS = 100
PAGE_SIZE = 20
TV_STATUS = {"ongoing": "0", "ended": "3|4"}


def item_key(item: dict[str, Any]) -> str:
    return f"{item['media_type']}:{item['tmdb_id']}"


def build_discover_params(
    recipe: Recipe, media_type: str, keyword_ids: list[int]
) -> dict[str, Any] | None:
    """TMDB discover params for one media type; None when the recipe cannot apply."""
    include, _ = genre_ids_for(recipe.genres, media_type)
    if recipe.genres and not include:
        return None  # e.g. a Thriller-only recipe has nothing to ask TV for
    params: dict[str, Any] = {
        "include_adult": "false",
        "vote_count.gte": recipe.min_votes,
        "sort_by": {
            "rating": "vote_average.desc",
            "popularity": "popularity.desc",
            "newest": (
                "primary_release_date.desc"
                if media_type == "movie"
                else "first_air_date.desc"
            ),
        }[recipe.sort_by],
    }
    if include:
        params["with_genres"] = "|".join(str(g) for g in include)
    exclude = genre_ids_for(recipe.genres_exclude, media_type)[0]
    if exclude:
        params["without_genres"] = ",".join(str(g) for g in exclude)
    if keyword_ids:
        params["with_keywords"] = "|".join(str(k) for k in keyword_ids)
    if recipe.min_rating is not None:
        params["vote_average.gte"] = recipe.min_rating
    if recipe.vote_count_max is not None:
        params["vote_count.lte"] = recipe.vote_count_max
    date_field = "primary_release_date" if media_type == "movie" else "first_air_date"
    if recipe.year_from:
        params[f"{date_field}.gte"] = f"{recipe.year_from}-01-01"
    if recipe.year_to:
        params[f"{date_field}.lte"] = f"{recipe.year_to}-12-31"
    if media_type == "movie":
        if recipe.runtime_min:
            params["with_runtime.gte"] = recipe.runtime_min
        if recipe.runtime_max:
            params["with_runtime.lte"] = recipe.runtime_max
    else:
        if recipe.episode_runtime_max:
            params["with_runtime.lte"] = recipe.episode_runtime_max
        if recipe.status in TV_STATUS:
            params["with_status"] = TV_STATUS[recipe.status]
    return params


class RecipeEngine:
    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def cache_key(self, collection: Collection, media_type: str, language: str) -> str:
        # A digest of everything an editor can change, not `updated_at`: Windows
        # clocks tick every ~15 ms, so a quick edit could keep the same timestamp
        # and keep serving the stale list.
        editable = json.dumps(
            [
                collection.recipe,
                collection.editor_pins,
                collection.editor_blocklist,
                collection.media_type,
                collection.reason_tr,
                collection.reason_en,
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(editable.encode()).hexdigest()[:16]
        return f"collection:v2:{collection.slug}:{digest}:{media_type}:{language}"

    def items(
        self, collection: Collection, media_type: str, language: str
    ) -> list[dict[str, Any]]:
        """All ranked items (≤ MAX_ITEMS), from cache when possible."""
        key = self.cache_key(collection, media_type, language)
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = self._generate(collection, media_type, language)
        cache.set(key, result, settings.COLLECTION_CACHE_TTL_SECONDS)
        return result

    def page(
        self, collection: Collection, media_type: str, language: str, page: int
    ) -> dict[str, Any]:
        items = self.items(collection, media_type, language)
        total_pages = max((len(items) + PAGE_SIZE - 1) // PAGE_SIZE, 1)
        start = (page - 1) * PAGE_SIZE
        return {
            "page": page,
            "total_pages": total_pages,
            "total_results": len(items),
            "results": items[start : start + PAGE_SIZE],
        }

    def random_pick(
        self,
        collection: Collection,
        media_type: str,
        language: str,
        exclude: set[str],
        rng: random.Random | None = None,
    ) -> dict[str, Any] | None:
        """One random title for the Lucky Globe, avoiding the caller's recent picks."""
        items = self.items(collection, media_type, language)
        pool = [i for i in items if item_key(i) not in exclude] or items
        return (rng or random).choice(pool) if pool else None

    # ------------------------------------------------------------------

    def _media_types(self, collection: Collection, requested: str) -> list[str]:
        allowed = (
            ["movie", "tv"]
            if collection.media_type == "both"
            else [collection.media_type]
        )
        if requested in ("movie", "tv"):
            return [requested] if requested in allowed else []
        return allowed

    def _generate(
        self, collection: Collection, requested: str, language: str
    ) -> list[dict[str, Any]]:
        recipe = collection.parsed_recipe()
        keyword_ids = self._resolve_keywords(recipe.keywords)
        blocked = set(collection.editor_blocklist)
        reason = collection.reason(language)

        candidates: dict[str, dict[str, Any]] = {}
        for media_type in self._media_types(collection, requested):
            params = build_discover_params(recipe, media_type, keyword_ids)
            if params is None:
                continue
            discover = (
                self._client.discover_movies
                if media_type == "movie"
                else self._client.discover_tv
            )
            excluded_ids = set(genre_ids_for(recipe.genres_exclude, media_type)[0])
            for page in range(1, recipe.pages + 1):
                data = discover({**params, "page": page}, language=language)
                for raw in data.get("results", []):
                    if (
                        raw.get("adult")
                        or set(raw.get("genre_ids") or []) & excluded_ids
                    ):
                        continue
                    item = format_tmdb_item(raw, default_media_type=media_type)
                    if item_key(item) not in blocked:
                        candidates.setdefault(item_key(item), item)
                if page >= (data.get("total_pages") or 1):
                    break

        ranked = sorted(
            candidates.values(), key=lambda i: self._score(i, recipe), reverse=True
        )
        pinned = self._pinned(collection, language, blocked)
        pinned_keys = {item_key(p) for p in pinned}
        ordered = pinned + [i for i in ranked if item_key(i) not in pinned_keys]
        for item in ordered:
            item["reason"] = reason
            item["pinned"] = item_key(item) in pinned_keys
        return ordered[:MAX_ITEMS]

    @staticmethod
    def _score(item: dict[str, Any], recipe: Recipe) -> float:
        if recipe.sort_by == "popularity":
            return float(item.get("popularity") or 0)
        if recipe.sort_by == "newest":
            return float((item.get("release_date") or "0000").replace("-", "")[:8] or 0)
        return bayesian_rating(
            float(item.get("vote_average") or 0),
            int(item.get("vote_count") or 0),
            item["media_type"],
        )

    def _pinned(
        self, collection: Collection, language: str, blocked: set[str]
    ) -> list[dict[str, Any]]:
        pinned = []
        for key in collection.editor_pins:
            if key in blocked:
                continue
            media_type, tmdb_id = key.split(":")
            fetch = (
                self._client.get_movie_detail
                if media_type == "movie"
                else self._client.get_tv_detail
            )
            try:
                data = fetch(int(tmdb_id), language=language)
            except TMDBNotFoundError:
                logger.warning("Pinned title %s not found on TMDB; skipped", key)
                continue
            data["genre_ids"] = [g["id"] for g in data.get("genres", []) if "id" in g]
            pinned.append(format_tmdb_item(data, default_media_type=media_type))
        return pinned

    def _resolve_keywords(self, keywords: list[str]) -> list[int]:
        ids: list[int] = []
        for keyword in keywords:
            results = self._client.search_keyword(keyword).get("results", [])
            exact = [r for r in results if r.get("name", "").lower() == keyword]
            if exact:
                ids.append(exact[0]["id"])
            elif results:
                ids.append(results[0]["id"])
        return list(dict.fromkeys(ids))
