"""Helpers that turn raw TMDB list items into CineGlobe's standard title payload."""

from typing import Any

from apps.catalog.image_utils import backdrop_url, poster_url


def format_tmdb_item(
    item: dict[str, Any], default_media_type: str = "movie"
) -> dict[str, Any]:
    """Format a raw TMDB list item (discover, search, credits) into a clean response item."""
    media_type = item.get("media_type") or default_media_type
    title_name = item.get("title") or item.get("name", "")
    rel_date = item.get("release_date") or item.get("first_air_date") or ""

    return {
        "media_type": media_type,
        "tmdb_id": item.get("id"),
        "title": title_name,
        "display_title": title_name,
        "original_title": item.get("original_title") or item.get("original_name", ""),
        "overview": item.get("overview", ""),
        "poster_url": poster_url(item.get("poster_path", "")),
        "backdrop_url": backdrop_url(item.get("backdrop_path", "")),
        "vote_average": item.get("vote_average", 0.0),
        "vote_count": item.get("vote_count", 0),
        "popularity": item.get("popularity", 0.0),
        "release_date": rel_date,
        "genre_ids": item.get("genre_ids", []),
    }
