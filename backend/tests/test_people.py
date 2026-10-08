"""Tests for People & Actor endpoints: Search, Profiles, and Chronological/Recent filmography."""

from unittest.mock import patch

from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from rest_framework import status


def test_person_search_missing_query(api_client):
    """Verify empty query param returns 400."""
    resp = api_client.get("/api/v1/people/search/?query=")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["error"]["code"] == "missing_query"


def test_person_search_success(api_client):
    """Verify valid actor search returns results."""
    mock_payload = {
        "results": [{"id": 3223, "name": "Robert Downey Jr.", "popularity": 85.0}]
    }

    with patch("apps.people.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.search_person.return_value = mock_payload

        resp = api_client.get("/api/v1/people/search/?query=RDJ")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Robert Downey Jr."


def test_person_detail_success_and_not_found(api_client):
    """Verify person details retrieval and 404 handling."""
    mock_details = {
        "id": 17419,
        "name": "Bryan Cranston",
        "biography": "American actor, producer and director.",
        "birthday": "1956-03-07",
        "place_of_birth": "Hollywood, California, USA",
        "profile_path": "/bryan.jpg",
        "popularity": 42.0,
    }

    with patch("apps.people.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_person_details.return_value = mock_details

        resp = api_client.get("/api/v1/people/17419/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "Bryan Cranston"
        assert "https://image.tmdb.org" in data["profile_url"]

        # Not found scenario
        mock_instance.get_person_details.side_effect = TMDBNotFoundError("Not found")
        resp_404 = api_client.get("/api/v1/people/999999/")
        assert resp_404.status_code == status.HTTP_404_NOT_FOUND


def test_person_credits_sorting_chronological_and_recent(api_client):
    """Verify filmography sorting: chronological_asc (oldest to newest) vs recent (newest first)."""
    mock_person = {"id": 100, "name": "Test Actor", "profile_path": "/test.jpg"}
    mock_credits = {
        "cast": [
            {
                "id": 1,
                "title": "Old Movie",
                "release_date": "1994-05-10",
                "media_type": "movie",
            },
            {
                "id": 2,
                "name": "Mid Series",
                "first_air_date": "2008-01-20",
                "media_type": "tv",
            },
            {
                "id": 3,
                "title": "Brand New Movie",
                "release_date": "2026-03-01",
                "media_type": "movie",
            },
        ]
    }

    with patch("apps.people.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_person_details.return_value = mock_person
        mock_instance.get_person_combined_credits.return_value = mock_credits

        # 1. Recent (newest first)
        resp_recent = api_client.get("/api/v1/people/100/credits/?sort_by=recent")
        assert resp_recent.status_code == status.HTTP_200_OK
        credits_recent = resp_recent.json()["credits"]
        assert credits_recent[0]["display_title"] == "Brand New Movie"
        assert credits_recent[-1]["display_title"] == "Old Movie"

        # 2. Chronological ascending (oldest to newest)
        resp_asc = api_client.get(
            "/api/v1/people/100/credits/?sort_by=chronological_asc"
        )
        assert resp_asc.status_code == status.HTTP_200_OK
        credits_asc = resp_asc.json()["credits"]
        assert credits_asc[0]["display_title"] == "Old Movie"
        assert credits_asc[-1]["display_title"] == "Brand New Movie"


def test_person_credits_media_type_filter(api_client):
    """Verify filtering filmography by media_type=tv or movie."""
    mock_person = {"id": 100, "name": "Test Actor"}
    mock_credits = {
        "cast": [
            {
                "id": 1,
                "title": "Movie A",
                "release_date": "2010-01-01",
                "media_type": "movie",
            },
            {
                "id": 2,
                "name": "TV Show B",
                "first_air_date": "2020-01-01",
                "media_type": "tv",
            },
        ]
    }

    with patch("apps.people.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_person_details.return_value = mock_person
        mock_instance.get_person_combined_credits.return_value = mock_credits

        # Only TV
        resp_tv = api_client.get("/api/v1/people/100/credits/?media_type=tv")
        assert resp_tv.status_code == status.HTTP_200_OK
        data_tv = resp_tv.json()
        assert data_tv["total_credits"] == 1
        assert data_tv["credits"][0]["media_type"] == "tv"
        assert data_tv["credits"][0]["display_title"] == "TV Show B"


def test_person_credits_tmdb_unavailable(api_client):
    """Verify TMDB error returns 503."""
    with patch("apps.people.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_person_details.side_effect = TMDBServiceUnavailableError(
            "Down"
        )

        resp = api_client.get("/api/v1/people/100/credits/")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
