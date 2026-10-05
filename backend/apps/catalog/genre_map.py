"""Genre mapping table: logical genre name → TMDB movie genre ID + TMDB TV genre ID.

TMDB uses separate integer IDs for movie genres vs TV genres.
This module provides a single source of truth mapping so the rest of the
system can reason about genres without caring about which ID space to use.

Usage:
    from apps.catalog.genre_map import GENRE_MAP, get_movie_genre_ids, get_tv_genre_ids

References:
    TMDB Movie genres:  https://api.themoviedb.org/3/genre/movie/list
    TMDB TV genres:     https://api.themoviedb.org/3/genre/tv/list
"""

from __future__ import annotations

# Each entry: logical_name → (movie_genre_id | None, tv_genre_id | None)
# None means the genre doesn't have a direct counterpart in that media type.
GENRE_MAP: dict[str, tuple[int | None, int | None]] = {
    # name              movie_id   tv_id
    "Action": (28, 10759),  # TV: "Action & Adventure"
    "Adventure": (12, 10759),  # TV: "Action & Adventure" (same bucket)
    "Animation": (16, 16),
    "Comedy": (35, 35),
    "Crime": (80, 80),
    "Documentary": (99, 99),
    "Drama": (18, 18),
    "Family": (10751, 10751),
    "Fantasy": (14, 10765),  # TV: "Sci-Fi & Fantasy"
    "History": (36, None),
    "Horror": (27, None),
    "Music": (10402, 10767),  # TV: "Talk" (closest bucket with music content)
    "Mystery": (9648, 9648),
    "News": (None, 10763),
    "Reality": (None, 10764),
    "Romance": (10749, None),
    "Science Fiction": (878, 10765),  # TV: "Sci-Fi & Fantasy"
    "Sci-Fi": (878, 10765),
    "Soap": (None, 10766),
    "Talk": (None, 10767),
    "Thriller": (53, None),  # TV doesn't have a dedicated Thriller genre
    "TV Movie": (10770, None),
    "War": (10752, 10768),  # TV: "War & Politics"
    "Western": (37, 37),
    "Kids": (None, 10762),
}


def get_movie_genre_ids(genre_names: list[str]) -> list[int]:
    """Return TMDB movie genre IDs for a list of logical genre names.

    Unknown names and genres without a movie counterpart are silently skipped.
    """
    ids: list[int] = []
    for name in genre_names:
        entry = GENRE_MAP.get(name)
        if entry and entry[0] is not None:
            ids.append(entry[0])
    return ids


def get_tv_genre_ids(genre_names: list[str]) -> list[int]:
    """Return TMDB TV genre IDs for a list of logical genre names.

    Unknown names and genres without a TV counterpart are silently skipped.
    """
    ids: list[int] = []
    for name in genre_names:
        entry = GENRE_MAP.get(name)
        if entry and entry[1] is not None:
            ids.append(entry[1])
    return ids


def genre_name_from_movie_id(tmdb_id: int) -> str | None:
    """Reverse-lookup: return the logical genre name for a TMDB movie genre ID."""
    for name, (movie_id, _) in GENRE_MAP.items():
        if movie_id == tmdb_id:
            return name
    return None


def genre_name_from_tv_id(tmdb_id: int) -> str | None:
    """Reverse-lookup: return the logical genre name for a TMDB TV genre ID."""
    for name, (_, tv_id) in GENRE_MAP.items():
        if tv_id == tmdb_id:
            return name
    return None
