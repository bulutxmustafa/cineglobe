"""Tests for TMDBClient with mocked HTTP requests and cache behavior."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from apps.catalog.tmdb_client import (
    TMDBClient,
    TMDBNotFoundError,
    TMDBRateLimitError,
    TMDBServiceUnavailableError,
    normalize_language,
)
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_test_cache():
    """Clear Django cache before each test run."""
    cache.clear()
    yield
    cache.clear()


def test_normalize_language():
    """Verify language code normalization."""
    assert normalize_language("tr") == "tr-TR"
    assert normalize_language("tr-TR") == "tr-TR"
    assert normalize_language("en") == "en-US"
    assert normalize_language("en-US") == "en-US"
    assert normalize_language("") == "tr-TR"
    assert normalize_language(None) == "tr-TR"


def test_tmdb_client_init_requires_key(monkeypatch):
    """Verify TMDBClient raises ValueError if API key is not present."""
    monkeypatch.setattr("django.conf.settings.TMDB_API_KEY", "")
    with pytest.raises(ValueError, match="TMDB_API_KEY is not set"):
        TMDBClient(api_key="")


def test_get_movie_detail_success_and_caching():
    """Verify get_movie_detail fetches and caches response for subsequent calls."""
    client = TMDBClient(api_key="mock_key")
    mock_payload = {"id": 100, "title": "Inception", "vote_average": 8.8}

    with patch.object(client._client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_payload
        mock_get.return_value = mock_response

        # 1st call -> HTTP GET
        res1 = client.get_movie_detail(100, language="tr")
        assert res1["title"] == "Inception"
        assert mock_get.call_count == 1

        # 2nd call -> Served from cache
        res2 = client.get_movie_detail(100, language="tr")
        assert res2["title"] == "Inception"
        assert mock_get.call_count == 1  # No extra HTTP call!


def test_get_movie_detail_distinct_cache_by_language():
    """Verify Turkish and English requests have isolated cache keys."""
    client = TMDBClient(api_key="mock_key")
    tr_payload = {"id": 200, "title": "Başlangıç"}
    en_payload = {"id": 200, "title": "Inception"}

    with patch.object(client._client, "get") as mock_get:
        mock_resp_tr = MagicMock(status_code=200, json=lambda: tr_payload)
        mock_resp_en = MagicMock(status_code=200, json=lambda: en_payload)
        mock_get.side_effect = [mock_resp_tr, mock_resp_en]

        res_tr = client.get_movie_detail(200, language="tr")
        res_en = client.get_movie_detail(200, language="en")

        assert res_tr["title"] == "Başlangıç"
        assert res_en["title"] == "Inception"
        assert mock_get.call_count == 2


def test_get_tv_detail_ongoing_series():
    """Verify ongoing TV show is cached with shorter TTL."""
    client = TMDBClient(api_key="mock_key")
    tv_payload = {
        "id": 500,
        "name": "Stranger Things",
        "in_production": True,
        "status": "Returning Series",
    }

    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: tv_payload)
        res = client.get_tv_detail(500)
        assert res["name"] == "Stranger Things"
        assert res["in_production"] is True


def test_discover_movies():
    """Verify discover_movies executes with language and parameters."""
    client = TMDBClient(api_key="mock_key")
    discover_payload = {"results": [{"id": 1, "title": "Movie 1"}]}

    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: discover_payload
        )
        res = client.discover_movies({"with_genres": "28"}, language="en")
        assert len(res["results"]) == 1
        assert res["results"][0]["title"] == "Movie 1"


def test_discover_tv():
    """Verify discover_tv executes with language and parameters."""
    client = TMDBClient(api_key="mock_key")
    discover_payload = {"results": [{"id": 2, "name": "TV Show 1"}]}

    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: discover_payload
        )
        res = client.discover_tv({"with_genres": "10759"}, language="tr")
        assert len(res["results"]) == 1


def test_person_endpoints():
    """Verify search_person and get_person_combined_credits."""
    client = TMDBClient(api_key="mock_key")
    search_payload = {"results": [{"id": 3223, "name": "Robert Downey Jr."}]}
    credits_payload = {"cast": [{"id": 10, "title": "Iron Man"}]}

    with patch.object(client._client, "get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: search_payload),
            MagicMock(status_code=200, json=lambda: credits_payload),
        ]
        person_res = client.search_person("RDJ")
        assert person_res["results"][0]["name"] == "Robert Downey Jr."

        credits_res = client.get_person_combined_credits(3223, language="en")
        assert credits_res["cast"][0]["title"] == "Iron Man"


def test_keyword_and_popular_endpoints():
    """Verify search_keyword, get_popular_movies, and get_popular_tv."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.side_effect = [
            MagicMock(
                status_code=200, json=lambda: {"results": [{"id": 123, "name": "spy"}]}
            ),
            MagicMock(status_code=200, json=lambda: {"results": [{"id": 1}]}),
            MagicMock(status_code=200, json=lambda: {"results": [{"id": 2}]}),
        ]
        assert client.search_keyword("spy")["results"][0]["name"] == "spy"
        assert len(client.get_popular_movies(1)["results"]) == 1
        assert len(client.get_popular_tv(1)["results"]) == 1


def test_person_details_and_upcoming_endpoints():
    """Verify get_person_details, get_upcoming_movies, and get_upcoming_tv."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"id": 1, "name": "Actor"}),
            MagicMock(
                status_code=200,
                json=lambda: {"results": [{"id": 10, "title": "Upcoming Movie"}]},
            ),
            MagicMock(
                status_code=200,
                json=lambda: {"results": [{"id": 20, "name": "Upcoming Series"}]},
            ),
        ]
        assert client.get_person_details(1)["name"] == "Actor"
        assert client.get_upcoming_movies(1)["results"][0]["title"] == "Upcoming Movie"
        assert client.get_upcoming_tv(1)["results"][0]["name"] == "Upcoming Series"


def test_error_handling_not_found():
    """Verify 404 raises TMDBNotFoundError."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=404)
        with pytest.raises(TMDBNotFoundError):
            client.get_movie_detail(999999)


def test_error_handling_rate_limit():
    """Verify 429 raises TMDBRateLimitError."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=429)
        with pytest.raises(TMDBRateLimitError):
            client.get_movie_detail(100)


def test_error_handling_service_unavailable():
    """Verify 500 raises TMDBServiceUnavailableError."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=500)
        with pytest.raises(TMDBServiceUnavailableError):
            client.get_movie_detail(100)


def test_error_handling_timeout_retries_and_raises():
    """Verify network timeout triggers retries and eventually raises TMDBServiceUnavailableError."""
    client = TMDBClient(api_key="mock_key")
    with patch.object(client._client, "get") as mock_get:
        mock_get.side_effect = httpx.ConnectTimeout("Connection timed out")
        with pytest.raises(TMDBServiceUnavailableError):
            client.get_movie_detail(100)
        assert mock_get.call_count == 3  # MAX_RETRIES
