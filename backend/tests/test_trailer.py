"""Trailer endpoint: best YouTube trailer, site language first, English fallback."""

from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from apps.catalog.views import pick_trailer
from django.core.cache import cache

URL = "/api/v1/titles/movie/680/trailer/"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _all_videos_play():
    """No real YouTube calls in tests; individual tests override this."""
    with patch("apps.catalog.views.youtube_playable", return_value=True) as playable:
        yield playable


def video(key, kind="Trailer", site="YouTube", official=True, lang="tr"):
    return {
        "key": key,
        "type": kind,
        "site": site,
        "official": official,
        "iso_639_1": lang,
        "name": key,
    }


def test_pick_trailer_prefers_official_youtube_trailer():
    videos = [
        video("clip", kind="Clip"),
        video("vimeo", site="Vimeo"),
        video("teaser", kind="Teaser"),
        video("fan", official=False),
        video("official"),
    ]
    assert pick_trailer(videos)["key"] == "official"
    assert pick_trailer([video("clip", kind="Clip")]) is None


def test_trailer_falls_back_to_english(api_client):
    client = MagicMock()
    client.get_videos.side_effect = lambda media_type, tmdb_id, language: {
        "results": [] if language == "tr-TR" else [video("en-key", lang="en")]
    }
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        response = api_client.get(URL, {"lang": "tr"})
    assert response.status_code == 200
    assert response.json()["trailer"]["key"] == "en-key"
    assert response.json()["trailer"]["language"] == "en"


def test_trailer_none_when_missing(api_client):
    client = MagicMock()
    client.get_videos.side_effect = TMDBNotFoundError("no title")
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        response = api_client.get(URL, {"lang": "tr"})
    assert response.status_code == 200
    assert response.json() == {"trailer": None}


def test_trailer_invalid_type_and_tmdb_down(api_client):
    assert api_client.get("/api/v1/titles/book/1/trailer/").status_code == 400
    client = MagicMock()
    client.get_videos.side_effect = TMDBServiceUnavailableError("down")
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        assert api_client.get(URL, {"lang": "tr"}).status_code == 503


def test_trailer_skips_deleted_youtube_videos(api_client, _all_videos_play):
    client = MagicMock()
    client.get_videos.side_effect = lambda media_type, tmdb_id, language: {
        "results": (
            [video("deleted")] if language == "tr-TR" else [video("ok", lang="en")]
        )
    }
    _all_videos_play.side_effect = lambda key: key != "deleted"
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        response = api_client.get(URL, {"lang": "tr"})
    assert response.json()["trailer"]["key"] == "ok"
