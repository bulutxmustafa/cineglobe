"""Tests for genre mapping between logical genre names and TMDB IDs."""

from apps.catalog.genre_map import (
    GENRE_MAP,
    genre_name_from_movie_id,
    genre_name_from_tv_id,
    get_movie_genre_ids,
    get_tv_genre_ids,
)


def test_genre_map_structure():
    """Verify GENRE_MAP contains essential genres with valid tuple structure."""
    assert "Action" in GENRE_MAP
    assert "Comedy" in GENRE_MAP
    assert "Drama" in GENRE_MAP
    assert "Science Fiction" in GENRE_MAP

    for name, (movie_id, tv_id) in GENRE_MAP.items():
        assert isinstance(name, str)
        if movie_id is not None:
            assert isinstance(movie_id, int)
        if tv_id is not None:
            assert isinstance(tv_id, int)


def test_get_movie_genre_ids():
    """Verify logical names map to correct TMDB movie genre IDs."""
    ids = get_movie_genre_ids(["Action", "Comedy", "NonExistentGenre"])
    assert 28 in ids  # Action
    assert 35 in ids  # Comedy
    assert len(ids) == 2


def test_get_tv_genre_ids():
    """Verify logical names map to correct TMDB TV genre IDs."""
    ids = get_tv_genre_ids(["Action", "Sci-Fi", "NonExistentGenre"])
    assert 10759 in ids  # Action & Adventure
    assert 10765 in ids  # Sci-Fi & Fantasy
    assert len(ids) == 2


def test_reverse_lookup_movie():
    """Verify movie TMDB genre ID maps back to logical name."""
    assert genre_name_from_movie_id(28) == "Action"
    assert genre_name_from_movie_id(18) == "Drama"
    assert genre_name_from_movie_id(999999) is None


def test_reverse_lookup_tv():
    """Verify TV TMDB genre ID maps back to logical name."""
    assert genre_name_from_tv_id(10759) in ("Action", "Adventure")
    assert genre_name_from_tv_id(10765) in ("Fantasy", "Science Fiction", "Sci-Fi")
    assert genre_name_from_tv_id(999999) is None
