"""Test doubles for the search pipeline: a fake Anthropic client and TMDB items."""

from __future__ import annotations

import json
import re
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from apps.search.explainer import Reason, ReasonList
from apps.search.schemas import SearchFilters


class FakeLLM:
    """Mimics `anthropic.Anthropic().messages.parse` for both pipeline calls.

    - SearchFilters requests return `filters` (or raise `parse_error`).
    - ReasonList requests echo back one reason per title key, plus any `extra_keys`.
    """

    def __init__(
        self,
        filters: SearchFilters | None = None,
        parse_error: Exception | None = None,
        stop_reason: str = "end_turn",
        explain_error: Exception | None = None,
        extra_keys: list[str] | None = None,
    ) -> None:
        self.filters = filters
        self.parse_error = parse_error
        self.stop_reason = stop_reason
        self.explain_error = explain_error
        self.extra_keys = extra_keys or []
        self.calls: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if kwargs["output_format"] is SearchFilters:
            if self.parse_error:
                raise self.parse_error
            return SimpleNamespace(
                stop_reason=self.stop_reason, parsed_output=self.filters
            )

        if self.explain_error:
            raise self.explain_error
        content = kwargs["messages"][0]["content"]
        language = re.search(r"<language>(\w+)</language>", content).group(1)
        titles = json.loads(
            re.search(r"<titles>\n(.*)\n</titles>", content, re.S).group(1)
        )
        keys = [t["key"] for t in titles] + self.extra_keys
        reasons = [
            Reason(key=k, reason=f"[{language}] LLM reason for {k}") for k in keys
        ]
        return SimpleNamespace(
            stop_reason="end_turn", parsed_output=ReasonList(reasons=reasons)
        )


def tmdb_item(
    tmdb_id: int,
    *,
    tv: bool = False,
    genre_ids: list[int] | None = None,
    rating: float = 7.5,
    votes: int = 5000,
    title: str | None = None,
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
