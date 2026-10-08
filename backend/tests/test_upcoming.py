"""Tests for Upcoming releases and reminder readiness endpoint."""

from datetime import date, timedelta
from unittest.mock import patch

from apps.catalog.tmdb_client import TMDBServiceUnavailableError
from rest_framework import status


def test_upcoming_titles_both_movie_and_tv(api_client):
    """Verify GET /api/v1/upcoming/ retrieves upcoming releases with countdown calculation."""
    future_date_1 = (date.today() + timedelta(days=15)).isoformat()
    future_date_2 = (date.today() + timedelta(days=30)).isoformat()

    mock_movies = {
        "results": [
            {
                "id": 801,
                "title": "Upcoming Blockbuster",
                "release_date": future_date_1,
                "poster_path": "/future_poster.jpg",
                "vote_average": 0.0,
            }
        ]
    }
    mock_tv = {
        "results": [
            {
                "id": 901,
                "name": "Upcoming SciFi Show",
                "first_air_date": future_date_2,
                "poster_path": "/future_tv.jpg",
                "vote_average": 0.0,
            }
        ]
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_upcoming_movies.return_value = mock_movies
        mock_instance.get_upcoming_tv.return_value = mock_tv

        resp = api_client.get("/api/v1/upcoming/?media_type=both")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["count"] == 2

    movie_item = next(i for i in data["results"] if i["tmdb_id"] == 801)
    assert movie_item["countdown_days"] == 15
    assert movie_item["is_unreleased"] is True
    assert movie_item["can_set_reminder"] is True

    tv_item = next(i for i in data["results"] if i["tmdb_id"] == 901)
    assert tv_item["countdown_days"] == 30
    assert tv_item["can_set_reminder"] is True


def test_upcoming_filter_movies_only(api_client):
    """Verify filtering by media_type=movie only invokes movie TMDB call."""
    mock_movies = {"results": [{"id": 1, "title": "Movie Only"}]}

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_upcoming_movies.return_value = mock_movies

        resp = api_client.get("/api/v1/upcoming/?media_type=movie")

    assert resp.status_code == status.HTTP_200_OK
    assert mock_instance.get_upcoming_movies.called
    assert not mock_instance.get_upcoming_tv.called


def test_upcoming_error_returns_503(api_client):
    """Verify TMDB error in upcoming view returns 503."""
    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_upcoming_movies.side_effect = TMDBServiceUnavailableError(
            "Down"
        )

        resp = api_client.get("/api/v1/upcoming/")

    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
