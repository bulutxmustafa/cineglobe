"""People services: best titles, full filmography and person detail (plan §3.2, §3.6)."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings

from apps.catalog.image_utils import poster_url, profile_url
from apps.catalog.tmdb_client import TMDBClient
from apps.people.credits import (
    credit_date,
    filter_role,
    has_enough_votes,
    is_lead,
    is_noise,
    merge_credits,
    sort_credits,
    split_upcoming,
)

TOP_LIMIT = 10
PAGE_SIZE = 20
KNOWN_FOR_LIMIT = 4


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.QUOTA_TIME_ZONE)).date()


def format_credit(item: dict[str, Any]) -> dict[str, Any]:
    media_type = item.get("media_type", "movie")
    released = credit_date(item)
    entry: dict[str, Any] = {
        "media_type": media_type,
        "tmdb_id": item.get("id"),
        "title": item.get("title") or item.get("name") or "",
        "original_title": item.get("original_title") or item.get("original_name") or "",
        "release_date": released,
        "year": int(released[:4]) if released[:4].isdigit() else None,
        "poster_url": poster_url(item.get("poster_path") or ""),
        "vote_average": item.get("vote_average") or 0.0,
        "vote_count": item.get("vote_count") or 0,
        "popularity": item.get("popularity") or 0.0,
        "characters": item.get("characters", []),
        "jobs": item.get("jobs", []),
        "is_lead": is_lead(item),
    }
    if media_type == "tv":
        first = item.get("first_credit_air_date") or ""
        entry["episode_count"] = item.get("episode_count") or 0
        # Year the person first appeared; the series' end year is not in this payload.
        entry["first_credit_year"] = int(first[:4]) if first[:4].isdigit() else None
    return entry


def title_reason(item: dict[str, Any], language: str) -> str:
    """Short template reason for a best-titles entry (no LLM, no cost)."""
    character = (item.get("characters") or [""])[0]
    rating = float(item.get("vote_average") or 0.0)
    votes = item.get("vote_count") or 0
    episodes = item.get("episode_count") or 0
    if language == "en":
        role = f"As {character}" if character else "In a leading role"
        extra = (
            f", {episodes} episodes"
            if item.get("media_type") == "tv" and episodes
            else ""
        )
        return f"{role}{extra} · TMDB {rating:.1f}/10 from {votes:,} votes."
    role = f"{character} rolüyle" if character else "Başrolde"
    extra = f", {episodes} bölüm" if item.get("media_type") == "tv" and episodes else ""
    votes_tr = f"{votes:,}".replace(",", ".")
    return f"{role}{extra} · TMDB'de {votes_tr} oyla {rating:.1f}/10."


class PeopleService:
    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    # ------------------------------------------------------------------

    def _cast(self, person_id: int, language: str) -> tuple[list, list]:
        data = self._client.get_person_combined_credits(person_id, language=language)
        # Crew stays raw: filter_role() filters by department before merging.
        return merge_credits(data.get("cast", [])), data.get("crew", [])

    def top_titles(
        self, person_id: int, media_type: str, language: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Best movies and/or series: lead roles, vote floor, no guest spots or noise."""
        cast, _ = self._cast(person_id, language)
        today = local_today().isoformat()
        eligible = [
            c
            for c in cast
            if not is_noise(c)
            and is_lead(c)
            and has_enough_votes(c)
            and credit_date(c)
            and credit_date(c) <= today
        ]
        sections: dict[str, list[dict[str, Any]]] = {}
        for mt in ("movie", "tv") if media_type == "both" else (media_type,):
            items = [c for c in eligible if c.get("media_type") == mt]
            items.sort(
                key=lambda c: (c.get("vote_average") or 0, c.get("vote_count") or 0),
                reverse=True,
            )
            sections["movies" if mt == "movie" else "series"] = [
                {**format_credit(c), "reason": title_reason(c, language)}
                for c in items[:TOP_LIMIT]
            ]
        return sections

    def filmography(
        self,
        person_id: int,
        *,
        sort: str,
        media_type: str,
        role: str,
        lead_only: bool,
        include_all: bool,
        page: int,
        language: str,
    ) -> dict[str, Any]:
        cast, crew = self._cast(person_id, language)
        items = filter_role(cast, crew, role)
        if media_type in ("movie", "tv"):
            items = [i for i in items if i.get("media_type") == media_type]
        hidden_noise = 0
        if not include_all:
            kept = [i for i in items if not is_noise(i)]
            hidden_noise = len(items) - len(kept)
            items = kept
        # Billing only exists for acting credits.
        if lead_only and role == "acting":
            items = [i for i in items if is_lead(i)]

        released, upcoming = split_upcoming(items, local_today())
        ordered = sort_credits(released, sort)
        total = len(ordered)
        total_pages = max(math.ceil(total / PAGE_SIZE), 1)
        start = (page - 1) * PAGE_SIZE
        return {
            "sort": sort,
            "media_type": media_type,
            "role": role,
            "lead_only": lead_only,
            "include_all": include_all,
            "page": page,
            "total_pages": total_pages,
            "total_results": total,
            "hidden_noise_count": hidden_noise,
            "results": [format_credit(i) for i in ordered[start : start + PAGE_SIZE]],
            # "Yakında": always complete and first on page 1 only.
            "upcoming": [format_credit(i) for i in upcoming] if page == 1 else [],
        }

    def detail(self, person_id: int, language: str) -> dict[str, Any]:
        data = self._client.get_person_details(person_id, language=language)
        biography = data.get("biography") or ""
        biography_language = language
        if not biography and language != "en":
            # Many people have no Turkish biography on TMDB (plan §3.4 fallback).
            english = self._client.get_person_details(person_id, language="en")
            biography = english.get("biography") or ""
            biography_language = "en" if biography else language

        birthday = data.get("birthday") or ""
        cast, _ = self._cast(person_id, language)
        known_for = sorted(
            (c for c in cast if not is_noise(c) and is_lead(c)),
            key=lambda c: c.get("vote_count") or 0,
            reverse=True,
        )[:KNOWN_FOR_LIMIT]
        return {
            "tmdb_id": data.get("id"),
            "name": data.get("name", ""),
            "biography": biography,
            "biography_language": biography_language,
            "biography_is_fallback": biography_language != language,
            "birthday": birthday or None,
            "birth_year": int(birthday[:4]) if birthday[:4].isdigit() else None,
            "deathday": data.get("deathday") or None,
            "place_of_birth": data.get("place_of_birth") or None,
            "known_for_department": data.get("known_for_department") or "",
            "profile_url": profile_url(data.get("profile_path") or ""),
            "known_for": [format_credit(c) for c in known_for],
        }
