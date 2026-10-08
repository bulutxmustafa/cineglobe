"""SearchService: parse → retrieve → rank → explain, with a per-query cache."""

from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any

from django.conf import settings
from django.core.cache import cache

from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.people.resolver import PersonResolver
from apps.people.services import PeopleService
from apps.search.explainer import brief, result_key, template_reason
from apps.search.ranker import Ranker
from apps.search.retriever import Retriever
from apps.search.router import LLMRouter, Quota
from apps.search.schemas import SearchFilters

CACHE_VERSION = "v2"
PUNCTUATION = re.compile(r"[^\w\s]")


class QueryNotUnderstoodError(Exception):
    """The query carries no usable viewing preference (maps to HTTP 400)."""

    def __init__(self, ai_status: str) -> None:
        super().__init__(ai_status)
        self.ai_status = ai_status


def normalize_query(query: str) -> str:
    """Case-, punctuation- and whitespace-insensitive form used for the cache key."""
    return " ".join(PUNCTUATION.sub(" ", query).split()).casefold()


def cache_key(query: str, media_type: str, language: str) -> str:
    # lang is part of the key: a Turkish explanation must never reach an English user.
    raw = json.dumps([normalize_query(query), media_type, language])
    return f"search:{CACHE_VERSION}:{hashlib.sha256(raw.encode()).hexdigest()}"


class SearchService:
    def __init__(
        self,
        router: LLMRouter | None = None,
        tmdb: TMDBClient | None = None,
    ) -> None:
        self._router = router
        self._tmdb = tmdb

    def search(
        self,
        query: str,
        media_type: str,
        language: str,
        quota: Quota | None = None,
    ) -> dict[str, Any]:
        key = cache_key(query, media_type, language)
        if (cached := cache.get(key)) is not None:
            return {**cached, "cached": True}

        started = time.monotonic()
        router = self._router or LLMRouter()
        parsed = router.parse(query, quota)
        filters = parsed.filters
        if not filters.is_meaningful:
            raise QueryNotUnderstoodError(parsed.ai_status)

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

        reasons = {result_key(i): template_reason(i, filters, language) for i in ranked}
        top_n = settings.LLM_EXPLAIN_TOP_N
        if parsed.ai_status == "ok" and top_n > 0:
            briefs = [brief(item) for item in ranked[:top_n]]
            reasons.update(router.explain(briefs, query, language))

        results = []
        for item in ranked:
            item = {k: v for k, v in item.items() if k != "matched_keywords"}
            item["reason"] = reasons[result_key(item)]
            results.append(item)

        payload = {
            "query": query,
            "lang": language,
            "media_type": filters.media_type,
            "parser": parsed.provider,
            "ai_status": parsed.ai_status,
            "filters": filters.public_dict(),
            "count": len(results),
            "results": results,
            "person": self._person_block(tmdb, filters, language),
            "took_ms": round((time.monotonic() - started) * 1000),
        }
        # Degraded answers (quota, budget, provider outage) are not cached, so the
        # same query gets AI quality again once the limit resets or the LLM recovers.
        if parsed.cacheable:
            cache.set(key, payload, settings.SEARCH_CACHE_TTL_SECONDS)
        return {**payload, "cached": False}

    @staticmethod
    def _person_block(
        tmdb: TMDBClient, filters: SearchFilters, language: str
    ) -> dict[str, Any] | None:
        """Best titles for "RDJ'nin en iyi filmleri"-style queries (plan Faz 4)."""
        if filters.intent != "person" or not filters.people:
            return None
        resolved = PersonResolver(tmdb).resolve(filters.people[0])
        if resolved.status != "found":
            # Not found / ambiguous: the client can call /people/top-titles/ to choose.
            return resolved.as_dict()
        sections = PeopleService(tmdb).top_titles(
            resolved.person["tmdb_id"], filters.media_type, language
        )
        return {
            **resolved.as_dict(),
            "media_type": filters.media_type,
            "sections": sections,
        }
