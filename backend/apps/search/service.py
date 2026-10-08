"""SearchService: parse → retrieve → rank → explain, with a per-query cache."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from django.conf import settings
from django.core.cache import cache

from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.search.explainer import Explainer, result_key
from apps.search.query_parser import QueryParser
from apps.search.ranker import Ranker
from apps.search.retriever import Retriever
from apps.search.schemas import SearchFilters

CACHE_VERSION = "v1"


class QueryNotUnderstoodError(Exception):
    """The query carries no usable viewing preference (maps to HTTP 400)."""


def normalize_query(query: str) -> str:
    return " ".join(query.split()).casefold()


def cache_key(query: str, media_type: str, language: str) -> str:
    # lang is part of the key: a Turkish explanation must never reach an English user.
    raw = json.dumps([normalize_query(query), media_type, language])
    return f"search:{CACHE_VERSION}:{hashlib.sha256(raw.encode()).hexdigest()}"


class SearchService:
    def __init__(
        self,
        parser: QueryParser | None = None,
        tmdb: TMDBClient | None = None,
        explainer: Explainer | None = None,
    ) -> None:
        self._parser = parser
        self._tmdb = tmdb
        self._explainer = explainer

    def search(self, query: str, media_type: str, language: str) -> dict[str, Any]:
        key = cache_key(query, media_type, language)
        if (cached := cache.get(key)) is not None:
            return {**cached, "cached": True}

        started = time.monotonic()
        parsed = (self._parser or QueryParser()).parse(query)
        filters = parsed.filters
        if not filters.is_meaningful:
            raise QueryNotUnderstoodError(query)

        # An explicit Film/Dizi toggle in the UI overrides what the text implied.
        # Re-validated so TV-only fields are cleared when the user forces "movie".
        if media_type != "both":
            filters = SearchFilters.model_validate(
                {**filters.model_dump(), "media_type": media_type}
            )

        try:
            tmdb = self._tmdb or TMDBClient()
        except ValueError as exc:  # TMDB_API_KEY missing
            raise TMDBError(str(exc)) from exc
        candidates = Retriever(tmdb).fetch(filters, language)
        ranked = Ranker().rank(candidates, filters)

        reasons = (self._explainer or Explainer()).explain(
            ranked, filters, query, language
        )
        results = []
        for item in ranked:
            item = {k: v for k, v in item.items() if k != "matched_keywords"}
            item["reason"] = reasons[result_key(item)]
            results.append(item)

        payload = {
            "query": query,
            "lang": language,
            "media_type": filters.media_type,
            "parser": parsed.source,
            "filters": filters.public_dict(),
            "count": len(results),
            "results": results,
            "took_ms": round((time.monotonic() - started) * 1000),
        }
        cache.set(key, payload, settings.SEARCH_CACHE_TTL_SECONDS)
        return {**payload, "cached": False}
