"""Test doubles for the search pipeline: a scriptable LLM provider and TMDB items."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from apps.search.providers.base import LLMProvider, LLMResult, TitleBrief
from apps.search.schemas import SearchFilters


class FakeProvider(LLMProvider):
    """An LLM provider whose answers and failures are scripted by the test.

    `parse_errors` are raised one by one on successive parse calls before the
    provider starts answering with `filters`. Every argument it receives is
    recorded in `received` so tests can prove what data reached the "LLM".
    """

    def __init__(
        self,
        name: str = "gemini",
        filters: SearchFilters | None = None,
        *,
        paid: bool = False,
        configured: bool = True,
        parse_errors: list[Exception] | None = None,
        explain_error: Exception | None = None,
        extra_reason_keys: list[str] | None = None,
        model: str = "fake-model",
        tokens: tuple[int, int] = (120, 40),
    ) -> None:
        self.name = name
        self.is_paid = paid
        self.filters = filters if filters is not None else SearchFilters()
        self._configured = configured
        self._parse_errors = list(parse_errors or [])
        self._explain_error = explain_error
        self._extra_keys = extra_reason_keys or []
        self.model = model
        self.tokens = tokens
        self.parse_calls: list[str] = []
        self.explain_calls: list[tuple[list[TitleBrief], str, str]] = []
        self.received: list[Any] = []

    def is_configured(self) -> bool:
        return self._configured

    def parse_query(self, query: str) -> LLMResult[SearchFilters]:
        self.parse_calls.append(query)
        self.received.append(query)
        if self._parse_errors:
            raise self._parse_errors.pop(0)
        return LLMResult(self.filters, self.model, *self.tokens)

    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> LLMResult[dict[str, str]]:
        self.explain_calls.append((titles, query, language))
        self.received.extend([[t.as_dict() for t in titles], query, language])
        if self._explain_error:
            raise self._explain_error
        keys = [t.key for t in titles] + self._extra_keys
        reasons = {k: f"[{language}] {self.name} reason for {k}" for k in keys}
        return LLMResult(reasons, self.model, *self.tokens)


def tmdb_item(
    tmdb_id: int,
    *,
    tv: bool = False,
    genre_ids: list[int] | None = None,
    rating: float = 7.5,
    votes: int = 5000,
    title: str | None = None,
    adult: bool = False,
) -> dict[str, Any]:
    name_key = "name" if tv else "title"
    date_key = "first_air_date" if tv else "release_date"
    return {
        "id": tmdb_id,
        name_key: title or f"{'Show' if tv else 'Movie'} {tmdb_id}",
        date_key: "2015-05-01",
        "overview": "An overview.",
        "poster_path": "/p.jpg",
        "backdrop_path": "/b.jpg",
        "vote_average": rating,
        "vote_count": votes,
        "popularity": 50.0,
        "genre_ids": genre_ids or [],
        "adult": adult,
    }


def fake_tmdb(
    movies: list[dict] | None = None,
    shows: list[dict] | None = None,
    keyword_results: dict[str, list[dict]] | None = None,
) -> MagicMock:
    client = MagicMock()
    client.discover_movies.return_value = {"results": movies or []}
    client.discover_tv.return_value = {"results": shows or []}
    keyword_results = keyword_results or {}
    client.search_keyword.side_effect = lambda q: {
        "results": keyword_results.get(q, [{"id": abs(hash(q)) % 100000, "name": q}])
    }
    client.search_person.return_value = {"results": [{"id": 3223, "name": "Person"}]}
    return client
