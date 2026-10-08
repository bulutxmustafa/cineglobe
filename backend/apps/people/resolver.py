"""Resolve a free-text person name to one TMDB person (plan §3.2, Faz 4).

Order: alias table → TMDB person search → surname search with fuzzy match
(typos such as "Brayn Cranston" return nothing from TMDB). When several people
share the name and none clearly dominates by popularity, candidates are
returned so the user can pick (e.g. "Chris Evans": the actor vs. the TV host).
The NL search parser (LLM) also expands nicknames before reaching this point.
"""

from __future__ import annotations

import difflib
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Literal

from apps.catalog.image_utils import profile_url
from apps.catalog.tmdb_client import TMDBClient

# Common nicknames TMDB search cannot resolve on its own. Lowercase keys.
ALIASES: dict[str, str] = {
    "rdj": "Robert Downey Jr.",
    "slj": "Samuel L. Jackson",
    "jlaw": "Jennifer Lawrence",
    "j.law": "Jennifer Lawrence",
    "scarjo": "Scarlett Johansson",
    "leo": "Leonardo DiCaprio",
    "dicaprio": "Leonardo DiCaprio",
    "the rock": "Dwayne Johnson",
    "arnie": "Arnold Schwarzenegger",
    "k-stew": "Kristen Stewart",
    "cumberbatch": "Benedict Cumberbatch",
}

# A same-name match is ambiguous unless the top hit is this much more popular.
DOMINANCE_RATIO = 3.0
FUZZY_MIN_RATIO = 0.8
MAX_CANDIDATES = 5


@dataclass
class ResolveResult:
    status: Literal["found", "ambiguous", "not_found"]
    person: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)
    query: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "query": self.query,
            "person": self.person,
            "candidates": self.candidates,
        }


def _fold(text: str) -> str:
    """Case/diacritic-insensitive form for comparing names."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(
        "".join(c for c in decomposed if not unicodedata.combining(c)).split()
    )


def summarize(person: dict[str, Any]) -> dict[str, Any]:
    return {
        "tmdb_id": person.get("id"),
        "name": person.get("name", ""),
        "known_for_department": person.get("known_for_department") or "",
        "profile_url": profile_url(person.get("profile_path") or ""),
        "known_for": [
            k.get("title") or k.get("name") or ""
            for k in (person.get("known_for") or [])[:3]
        ],
        "popularity": person.get("popularity") or 0.0,
    }


class PersonResolver:
    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def resolve(self, name: str) -> ResolveResult:
        query = " ".join(name.split())
        target = ALIASES.get(_fold(query), query)

        results = self._search(target)
        if not results:
            results = self._fuzzy_by_surname(target)
        if not results:
            return ResolveResult("not_found", query=query)

        folded = _fold(target)
        exact = [p for p in results if _fold(p.get("name", "")) == folded]
        pool = exact or results
        pool.sort(key=lambda p: p.get("popularity") or 0, reverse=True)
        top = pool[0]

        if len(pool) > 1:
            second = pool[1].get("popularity") or 0
            dominant = (top.get("popularity") or 0) >= DOMINANCE_RATIO * max(
                second, 0.01
            )
            if not dominant:
                return ResolveResult(
                    "ambiguous",
                    candidates=[summarize(p) for p in pool[:MAX_CANDIDATES]],
                    query=query,
                )

        others = [summarize(p) for p in pool[1:MAX_CANDIDATES]]
        return ResolveResult("found", summarize(top), others, query=query)

    def _search(self, name: str) -> list[dict[str, Any]]:
        results = self._client.search_person(name).get("results", [])
        return [p for p in results if not p.get("adult")]

    def _fuzzy_by_surname(self, name: str) -> list[dict[str, Any]]:
        parts = name.split()
        if len(parts) < 2:
            return []
        surname = max(parts, key=len)
        folded = _fold(name)
        return [
            p
            for p in self._search(surname)
            if difflib.SequenceMatcher(None, folded, _fold(p.get("name", ""))).ratio()
            >= FUZZY_MIN_RATIO
        ]
