"""Collection recipe schema (plan §3.5): the rule a curated collection is generated from.

A recipe is stored as JSON on the Collection model and validated with Pydantic
both in the admin (model.clean) and before use, so a typo cannot break a page.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from apps.search.schemas import Genre

SortBy = Literal["rating", "popularity", "newest"]


class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Any of these genres (OR). Missing genres in a media type use stand-ins.
    genres: list[Genre] = []
    # Hard exclusion: applied in the TMDB query and again on every result.
    genres_exclude: list[Genre] = []
    # English TMDB keywords, any of them (OR).
    keywords: list[str] = []
    runtime_min: int | None = None
    runtime_max: int | None = None
    min_rating: float | None = None
    min_votes: int = 500
    vote_count_max: int | None = None
    year_from: int | None = None
    year_to: int | None = None
    episode_runtime_max: int | None = None
    status: Literal["ongoing", "ended", "any"] = "any"
    sort_by: SortBy = "rating"
    # TMDB pages fetched per media type to build the candidate pool (20 per page).
    pages: int = 3

    @field_validator("keywords")
    @classmethod
    def _clean_keywords(cls, values: list[str]) -> list[str]:
        cleaned = [" ".join(v.split()).lower() for v in values]
        return list(dict.fromkeys(v for v in cleaned if v))[:8]

    @field_validator("pages")
    @classmethod
    def _pages_range(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("pages must be between 1 and 5")
        return value

    @field_validator("min_votes")
    @classmethod
    def _non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("min_votes must be >= 0")
        return value

    @field_validator("min_rating")
    @classmethod
    def _rating_range(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 10:
            raise ValueError("min_rating must be between 0 and 10")
        return value

    @model_validator(mode="after")
    def _consistent(self) -> Recipe:
        if set(self.genres) & set(self.genres_exclude):
            raise ValueError("a genre cannot be both included and excluded")
        for low, high, name in (
            (self.runtime_min, self.runtime_max, "runtime"),
            (self.year_from, self.year_to, "year"),
            (self.min_votes, self.vote_count_max, "vote count"),
        ):
            if low is not None and high is not None and low > high:
                raise ValueError(f"{name} minimum is greater than its maximum")
        return self
