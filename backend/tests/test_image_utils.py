"""Tests for TMDB image URL generation helpers."""

from apps.catalog.image_utils import (
    DEFAULT_BACKDROP_SIZE,
    DEFAULT_POSTER_SIZE,
    DEFAULT_PROFILE_SIZE,
    TMDB_IMAGE_BASE,
    backdrop_url,
    poster_url,
    profile_url,
)


def test_poster_url_valid_path():
    """Verify poster URL uses default size token."""
    url = poster_url("/test_poster.jpg")
    assert url == f"{TMDB_IMAGE_BASE}/{DEFAULT_POSTER_SIZE}/test_poster.jpg"


def test_poster_url_custom_size():
    """Verify custom valid size token is respected."""
    url = poster_url("/test_poster.jpg", size="w780")
    assert url == f"{TMDB_IMAGE_BASE}/w780/test_poster.jpg"


def test_poster_url_invalid_size_fallback():
    """Verify invalid size falls back to default."""
    url = poster_url("/test_poster.jpg", size="invalid_size")
    assert url == f"{TMDB_IMAGE_BASE}/{DEFAULT_POSTER_SIZE}/test_poster.jpg"


def test_backdrop_url():
    """Verify backdrop URL formatting."""
    url = backdrop_url("/test_backdrop.jpg")
    assert url == f"{TMDB_IMAGE_BASE}/{DEFAULT_BACKDROP_SIZE}/test_backdrop.jpg"


def test_profile_url():
    """Verify person profile URL formatting."""
    url = profile_url("/test_person.jpg")
    assert url == f"{TMDB_IMAGE_BASE}/{DEFAULT_PROFILE_SIZE}/test_person.jpg"


def test_empty_paths_return_empty_string():
    """Verify falsy or empty paths return empty string without error."""
    assert poster_url("") == ""
    assert poster_url(None) == ""
    assert backdrop_url("") == ""
    assert profile_url("") == ""
