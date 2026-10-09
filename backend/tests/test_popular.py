"""Popular titles endpoint (home page poster wall)."""

from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBServiceUnavailableError
from django.core.cache import cache

URL = "/api/v1/popular/"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def item(tmdb_id, popularity, poster="/p.jpg", genres=(18,)):
    return {
        "id": tmdb_id,
        "title": f"T{tmdb_id}",
        "name": f"T{tmdb_id}",
        "popularity": popularity,
        "poster_path": poster,
        "genre_ids": list(genres),
    }


def client_with(movies, tv):
    client = MagicMock()
    client.get_popular_movies.return_value = {"results": movies}
    client.get_popular_tv.return_value = {"results": tv}
    return patch("apps.catalog.views.TMDBClient", return_value=client)


def test_popular_merges_sorts_and_skips_posterless(api_client):
    with client_with([item(1, 50), item(2, 90, poster=None)], [item(3, 70)]):
        data = api_client.get(URL, {"lang": "tr"}).json()
    assert [r["tmdb_id"] for r in data["results"]] == [3, 1]
    assert {r["media_type"] for r in data["results"]} == {"movie", "tv"}


def test_popular_media_type_filter_and_cdn_header(api_client):
    with client_with([item(1, 50)], [item(3, 70)]):
        response = api_client.get(URL, {"media_type": "movie", "lang": "en"})
    assert [r["tmdb_id"] for r in response.json()["results"]] == [1]
    assert "s-maxage=3600" in response["Cache-Control"]


def test_popular_invalid_media_type(api_client):
    assert api_client.get(URL, {"media_type": "x"}).status_code == 400


def test_popular_tmdb_down(api_client):
    client = MagicMock()
    client.get_popular_movies.side_effect = TMDBServiceUnavailableError("down")
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        assert api_client.get(URL).status_code == 503


def test_popular_skips_talk_and_reality_shows(api_client):
    with client_with(
        [item(1, 50)], [item(3, 99, genres=(10767,)), item(4, 60, genres=(10764, 35))]
    ):
        data = api_client.get(URL).json()
    assert [r["tmdb_id"] for r in data["results"]] == [1]
