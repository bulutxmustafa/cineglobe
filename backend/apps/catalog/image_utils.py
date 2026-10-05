"""TMDB image URL helpers.

TMDB returns bare path strings like '/abc123.jpg'. This module converts them
to full URLs using configurable size tokens.

Reference: https://developer.themoviedb.org/docs/image-basics
"""

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"

# Available poster sizes (width-based)
POSTER_SIZES = ["w92", "w154", "w185", "w342", "w500", "w780", "original"]

# Available backdrop sizes (width-based)
BACKDROP_SIZES = ["w300", "w780", "w1280", "original"]

# Available profile (person) sizes
PROFILE_SIZES = ["w45", "w185", "h632", "original"]

# Default sizes used by the API responses
DEFAULT_POSTER_SIZE = "w500"
DEFAULT_BACKDROP_SIZE = "w1280"
DEFAULT_PROFILE_SIZE = "w185"


def poster_url(path: str, size: str = DEFAULT_POSTER_SIZE) -> str:
    """Build the full TMDB poster image URL.

    Args:
        path: The bare path string from TMDB (e.g. '/abc123.jpg').
        size: A valid TMDB poster size token. Defaults to 'w500'.

    Returns:
        Full URL string, or empty string if path is falsy.
    """
    if not path:
        return ""
    if size not in POSTER_SIZES:
        size = DEFAULT_POSTER_SIZE
    return f"{TMDB_IMAGE_BASE}/{size}{path}"


def backdrop_url(path: str, size: str = DEFAULT_BACKDROP_SIZE) -> str:
    """Build the full TMDB backdrop image URL.

    Args:
        path: The bare path string from TMDB.
        size: A valid TMDB backdrop size token. Defaults to 'w1280'.

    Returns:
        Full URL string, or empty string if path is falsy.
    """
    if not path:
        return ""
    if size not in BACKDROP_SIZES:
        size = DEFAULT_BACKDROP_SIZE
    return f"{TMDB_IMAGE_BASE}/{size}{path}"


def profile_url(path: str, size: str = DEFAULT_PROFILE_SIZE) -> str:
    """Build the full TMDB person profile image URL.

    Args:
        path: The bare path string from TMDB.
        size: A valid TMDB profile size token. Defaults to 'w185'.

    Returns:
        Full URL string, or empty string if path is falsy.
    """
    if not path:
        return ""
    if size not in PROFILE_SIZES:
        size = DEFAULT_PROFILE_SIZE
    return f"{TMDB_IMAGE_BASE}/{size}{path}"
