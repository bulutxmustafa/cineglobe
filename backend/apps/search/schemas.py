"""Pydantic schemas for natural-language search filters.

`SearchFilters` is both the structured-output schema the LLM must fill in and
the validated filter object the rest of the pipeline consumes. Validators clamp
or drop unsafe values instead of raising, so a slightly-off LLM answer still
produces a usable search (the fallback parser builds the same object).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

from apps.catalog.genre_map import GENRE_MAP

# Logical genre names the LLM may use; mapped to TMDB IDs by the retriever.
Genre = Literal[tuple(GENRE_MAP)]  # type: ignore[valid-type]

MediaType = Literal["movie", "tv", "both"]

MAX_KEYWORDS = 6
MAX_PEOPLE = 3
MIN_YEAR = 1900
MAX_YEAR = 2100


class SearchFilters(BaseModel):
    """Structured filters extracted from a free-text movie/TV request."""

    is_meaningful: bool = True
    intent: Literal["discover", "person"] = "discover"
    media_type: MediaType = "both"
    genres_include: list[Genre] = []
    genres_exclude: list[Genre] = []
    keywords: list[str] = []
    moods: list[str] = []
    people: list[str] = []
    year_from: int | None = None
    year_to: int | None = None
    min_rating: float | None = None
    runtime_max: int | None = None
    episode_runtime_max: int | None = None
    max_seasons: int | None = None
    status: Literal["ongoing", "ended", "any"] = "any"
    language_hint: Literal["tr", "en"] = "tr"

    @field_validator("keywords", "moods", "people")
    @classmethod
    def _clean_strings(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            text = " ".join(str(value).split())[:60].lower()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned

    @field_validator("genres_include", "genres_exclude")
    @classmethod
    def _dedupe_genres(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    @field_validator("min_rating")
    @classmethod
    def _clamp_rating(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return min(max(float(value), 0.0), 9.0)

    @field_validator("year_from", "year_to")
    @classmethod
    def _valid_year(cls, value: int | None) -> int | None:
        if value is None or not MIN_YEAR <= value <= MAX_YEAR:
            return None
        return value

    @field_validator("runtime_max", "episode_runtime_max", "max_seasons")
    @classmethod
    def _positive_or_none(cls, value: int | None) -> int | None:
        return value if value is not None and value > 0 else None

    @model_validator(mode="after")
    def _resolve_conflicts(self) -> SearchFilters:
        # An explicit exclusion always wins over an inclusion of the same genre.
        self.genres_include = [
            g for g in self.genres_include if g not in self.genres_exclude
        ]
        self.keywords = self.keywords[:MAX_KEYWORDS]
        self.people = self.people[:MAX_PEOPLE]
        if self.year_from and self.year_to and self.year_from > self.year_to:
            self.year_from, self.year_to = self.year_to, self.year_from
        # TV-only constraints make no sense for a movie-only search.
        if self.media_type == "movie":
            self.episode_runtime_max = None
            self.max_seasons = None
            self.status = "any"
        return self

    def has_signal(self) -> bool:
        """True when the filters carry anything to search on."""
        return bool(
            self.genres_include
            or self.genres_exclude
            or self.keywords
            or self.moods
            or self.people
            or self.year_from
            or self.year_to
            or self.media_type != "both"
        )

    def public_dict(self) -> dict:
        """Filters as returned to API clients ('applied filters')."""
        return self.model_dump(exclude={"is_meaningful"})


class Reason(BaseModel):
    key: str
    reason: str


class ReasonList(BaseModel):
    """Structured-output schema for batched "why was this recommended?" lines."""

    reasons: list[Reason]

    def as_mapping(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for entry in self.reasons:
            text = " ".join(entry.reason.split())
            if text:
                mapping[entry.key] = text
        return mapping
