"""Pure helpers for TMDB combined_credits: merge, clean, classify and sort (plan §3.2, §3.6).

Facts about the TMDB payload this module relies on (checked against live data):
- one title can appear several times (several characters or jobs) → merged here;
- TV cast credits have no billing `order`, but carry `episode_count` and
  `first_credit_air_date`; movie cast credits carry `order`;
- appearances as oneself (`Self`, `Himself`, archive footage) are common noise.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date
from typing import Any, Literal

from django.conf import settings

SortMode = Literal["newest", "oldest", "rating", "popularity"]
SORT_MODES: tuple[str, ...] = ("newest", "oldest", "rating", "popularity")

# Roles that are not acting performances.
NOISE_CHARACTER = re.compile(
    r"\b(self|himself|herself|themselves|archive footage|archival footage|uncredited)\b",
    re.IGNORECASE,
)
# TV genres that are not scripted shows: Talk, News, Reality.
NOISE_TV_GENRES = {10767, 10763, 10764}

# Crew department → role filter value.
ROLE_DEPARTMENTS = {
    "directing": {"Directing"},
    "production": {"Production"},
    "writing": {"Writing"},
}
ROLES: tuple[str, ...] = ("acting", "directing", "production", "writing")


def credit_date(item: dict[str, Any]) -> str:
    """ISO date of the title (movie release or series premiere), '' when unknown."""
    return item.get("release_date") or item.get("first_air_date") or ""


def merge_credits(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per (media_type, id); characters/jobs joined, best billing kept."""
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for item in items:
        key = (item.get("media_type", "movie"), item.get("id"))
        current = merged.get(key)
        if current is None:
            entry = dict(item)
            entry["characters"] = _non_empty([item.get("character")])
            entry["jobs"] = _non_empty([item.get("job")])
            merged[key] = entry
            continue
        current["characters"] = _non_empty(
            [*current["characters"], item.get("character")]
        )
        current["jobs"] = _non_empty([*current["jobs"], item.get("job")])
        current["episode_count"] = max(
            current.get("episode_count") or 0, item.get("episode_count") or 0
        )
        orders = [o for o in (current.get("order"), item.get("order")) if o is not None]
        current["order"] = min(orders) if orders else None
    return list(merged.values())


def _non_empty(values: Iterable[str | None]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen


def is_noise(item: dict[str, Any]) -> bool:
    """Self/archive/uncredited appearances and talk/news/reality TV."""
    if item.get("adult"):
        return True
    characters = item.get("characters") or [item.get("character") or ""]
    if characters and all(NOISE_CHARACTER.search(c or "") for c in characters):
        return True
    return item.get("media_type") == "tv" and bool(
        set(item.get("genre_ids") or []) & NOISE_TV_GENRES
    )


def is_lead(item: dict[str, Any]) -> bool:
    """Top-5 billing for movies; a recurring role (not a guest spot) for series."""
    if item.get("media_type") == "tv":
        return (item.get("episode_count") or 0) >= settings.PERSON_MIN_EPISODES
    order = item.get("order")
    return order is not None and order <= settings.PERSON_LEAD_MAX_ORDER


def sort_credits(items: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    """Sort by mode; undated titles always go last (they never raise)."""
    dated = [i for i in items if credit_date(i)]
    undated = [i for i in items if not credit_date(i)]
    if mode == "oldest":
        dated.sort(key=credit_date)
    elif mode == "rating":
        # Rating with a vote floor so a 10.0 from 3 votes does not lead.
        dated.sort(
            key=lambda i: (has_enough_votes(i), i.get("vote_average") or 0),
            reverse=True,
        )
        undated.sort(
            key=lambda i: (has_enough_votes(i), i.get("vote_average") or 0),
            reverse=True,
        )
    elif mode == "popularity":
        dated.sort(key=lambda i: i.get("popularity") or 0, reverse=True)
        undated.sort(key=lambda i: i.get("popularity") or 0, reverse=True)
    else:  # newest
        dated.sort(key=credit_date, reverse=True)
    return dated + undated


def has_enough_votes(item: dict[str, Any]) -> bool:
    floor = (
        settings.PERSON_MIN_VOTES_TV
        if item.get("media_type") == "tv"
        else settings.PERSON_MIN_VOTES_MOVIE
    )
    return (item.get("vote_count") or 0) >= floor


def split_upcoming(
    items: list[dict[str, Any]], today: date
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(released or undated, future-dated). Future titles go to the 'Yakında' group."""
    today_iso = today.isoformat()
    released = [i for i in items if not credit_date(i) or credit_date(i) <= today_iso]
    upcoming = [i for i in items if credit_date(i) and credit_date(i) > today_iso]
    upcoming.sort(key=credit_date)
    return released, upcoming


def filter_role(
    cast: list[dict[str, Any]], crew: list[dict[str, Any]], role: str
) -> list[dict[str, Any]]:
    """Merged credits for one role. Crew is filtered by department *before* merging,
    so a title where the person both directed and produced lists only the
    jobs of the requested role."""
    if role == "acting":
        return cast
    departments = ROLE_DEPARTMENTS[role]
    return merge_credits(c for c in crew if c.get("department") in departments)
