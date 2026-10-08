"""Template "why was this recommended?" reasons and the title briefs sent to LLMs.

Every result gets a deterministic, localized template reason (no LLM, no cost).
Only the top few results are upgraded to LLM-written reasons by the router
(plan §3.10). `brief()` defines exactly which title data an LLM may see.
"""

from __future__ import annotations

from typing import Any

from apps.catalog.genre_map import genre_name_from_movie_id, genre_name_from_tv_id
from apps.search.providers.base import TitleBrief
from apps.search.schemas import SearchFilters

GENRE_NAMES_TR = {
    "Action": "aksiyon",
    "Adventure": "macera",
    "Animation": "animasyon",
    "Comedy": "komedi",
    "Crime": "suç",
    "Documentary": "belgesel",
    "Drama": "dram",
    "Family": "aile",
    "Fantasy": "fantastik",
    "History": "tarih",
    "Horror": "korku",
    "Music": "müzik",
    "Mystery": "gizem",
    "News": "haber",
    "Reality": "reality",
    "Romance": "romantik",
    "Science Fiction": "bilim kurgu",
    "Sci-Fi": "bilim kurgu",
    "Soap": "pembe dizi",
    "Talk": "talk show",
    "Thriller": "gerilim",
    "TV Movie": "TV filmi",
    "War": "savaş",
    "Western": "western",
    "Kids": "çocuk",
}


def result_key(item: dict[str, Any]) -> str:
    return f"{item['media_type']}:{item['tmdb_id']}"


def _genre_names(item: dict[str, Any]) -> list[str]:
    lookup = (
        genre_name_from_movie_id
        if item["media_type"] == "movie"
        else genre_name_from_tv_id
    )
    names = [lookup(g) for g in item.get("genre_ids") or []]
    return [n for n in names if n]


def template_reason(item: dict[str, Any], filters: SearchFilters, language: str) -> str:
    """Deterministic reason used when the LLM is unavailable."""
    genres = _genre_names(item)[:2]
    rating = float(item.get("vote_average") or 0.0)
    is_tv = item["media_type"] == "tv"

    if language == "en":
        kind = "series" if is_tv else "film"
        genre_text = f"{' / '.join(g.lower() for g in genres)} " if genres else ""
        text = f"A {genre_text}{kind} rated {rating:.1f}/10 on TMDB"
        if item.get("matched_keywords") and filters.keywords:
            text += f", matching themes like {', '.join(filters.keywords[:2])}"
        return text + "."

    kind = "dizi" if is_tv else "film"
    genre_text = (
        f"{' / '.join(GENRE_NAMES_TR.get(g, g) for g in genres)} türünde "
        if genres
        else ""
    )
    text = f"TMDB'de {rating:.1f}/10 puanlı, {genre_text}bir {kind}"
    if item.get("matched_keywords") and filters.keywords:
        text += "; aradığın temalarla örtüşüyor"
    return text + "."


def brief(item: dict[str, Any]) -> TitleBrief:
    """Public catalogue metadata for one result: the only title data an LLM receives."""
    return TitleBrief(
        key=result_key(item),
        media_type=item["media_type"],
        title=item.get("title", ""),
        year=(item.get("release_date") or "")[:4],
        genres=_genre_names(item),
        rating=item.get("vote_average"),
        overview=(item.get("overview") or "")[:300],
    )
