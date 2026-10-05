"""Tests for Catalog API endpoints verifying Faz 2 acceptance criteria.

Criteria:
1. GET /api/v1/titles/{media_type}/{tmdb_id}/ works and caches.
2. A movie and a TV show with the SAME tmdb_id do NOT overwrite each other.
3. When TMDB is down, API returns meaningful 503 instead of 500.
4. When TMDB returns 404, API returns structured 404.
5. Invalid media_type returns 400.
6. Multi-language (TR/EN) parameter works as requested.
"""

from unittest.mock import patch

import pytest
from apps.catalog.models import Title
from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from django.core.cache import cache
from rest_framework import status


@pytest.fixture(autouse=True)
def clean_database_and_cache():
    """Ensure tests run against a clean database and cache."""
    cache.clear()
    Title.objects.all().delete()
    yield
    cache.clear()


@pytest.mark.django_db
def test_title_detail_movie_success(api_client):
    """Verify movie detail endpoint returns 200 with structured title data."""
    mock_movie = {
        "id": 550,
        "title": "Dövüş Kulübü",
        "original_title": "Fight Club",
        "overview": "Birinci kural: Dövüş Kulübü hakkında konuşma.",
        "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "backdrop_path": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
        "original_language": "en",
        "vote_average": 8.4,
        "vote_count": 27000,
        "popularity": 95.5,
        "release_date": "1999-10-15",
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_movie_detail.return_value = mock_movie

        response = api_client.get("/api/v1/titles/movie/550/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tmdb_id"] == 550
    assert data["media_type"] == "movie"
    assert data["title"] == "Dövüş Kulübü"
    assert "https://image.tmdb.org" in data["poster_url"]
    assert Title.objects.filter(media_type="movie", tmdb_id=550).exists()


@pytest.mark.django_db
def test_title_detail_tv_success(api_client):
    """Verify TV detail endpoint returns 200 with structured TV data."""
    mock_tv = {
        "id": 1396,
        "name": "Breaking Bad",
        "original_name": "Breaking Bad",
        "overview": "Kimya öğretmeni Walter White...",
        "poster_path": "/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
        "backdrop_path": "/tsRy63Mu5cu8etL1X7ZLyf7UP1M.jpg",
        "original_language": "en",
        "vote_average": 9.3,
        "vote_count": 14000,
        "popularity": 180.2,
        "first_air_date": "2008-01-20",
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_tv_detail.return_value = mock_tv

        response = api_client.get("/api/v1/titles/tv/1396/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tmdb_id"] == 1396
    assert data["media_type"] == "tv"
    assert data["title"] == "Breaking Bad"


@pytest.mark.django_db
def test_same_tmdb_id_movie_and_tv_do_not_collide(api_client):
    """CRITICAL TEST: Ensure a movie and a TV show with the exact same tmdb_id co-exist.

    Both must have their own independent records in DB and separate API responses.
    """
    shared_id = 9999

    movie_data = {
        "id": shared_id,
        "title": "Awesome Movie 9999",
        "overview": "This is a movie.",
        "vote_average": 7.5,
    }
    tv_data = {
        "id": shared_id,
        "name": "Awesome TV Series 9999",
        "overview": "This is a TV series.",
        "vote_average": 8.9,
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_movie_detail.return_value = movie_data
        mock_instance.get_tv_detail.return_value = tv_data

        # Fetch movie
        resp_movie = api_client.get(f"/api/v1/titles/movie/{shared_id}/")
        assert resp_movie.status_code == status.HTTP_200_OK
        assert resp_movie.json()["title"] == "Awesome Movie 9999"
        assert resp_movie.json()["media_type"] == "movie"

        # Fetch TV show with the same ID
        resp_tv = api_client.get(f"/api/v1/titles/tv/{shared_id}/")
        assert resp_tv.status_code == status.HTTP_200_OK
        assert resp_tv.json()["title"] == "Awesome TV Series 9999"
        assert resp_tv.json()["media_type"] == "tv"

    # Verify both separate rows exist in the database!
    movie_obj = Title.objects.get(media_type="movie", tmdb_id=shared_id)
    tv_obj = Title.objects.get(media_type="tv", tmdb_id=shared_id)

    assert movie_obj.id != tv_obj.id
    assert movie_obj.title == "Awesome Movie 9999"
    assert tv_obj.title == "Awesome TV Series 9999"
    assert Title.objects.filter(tmdb_id=shared_id).count() == 2


@pytest.mark.django_db
def test_title_detail_tmdb_unavailable_returns_503(api_client):
    """Verify that when TMDB fails, API returns meaningful 503 instead of 500."""
    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_movie_detail.side_effect = TMDBServiceUnavailableError(
            "TMDB timeout or 5xx outage"
        )

        response = api_client.get("/api/v1/titles/movie/100/")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "service_unavailable"
    assert "erişilemiyor" in data["error"]["message"]


@pytest.mark.django_db
def test_title_detail_not_found_returns_404(api_client):
    """Verify missing TMDB title returns structured 404."""
    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_movie_detail.side_effect = TMDBNotFoundError("Not found")

        response = api_client.get("/api/v1/titles/movie/99999999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["error"]["code"] == "not_found"


@pytest.mark.django_db
def test_title_detail_invalid_media_type_returns_400(api_client):
    """Verify invalid media_type parameter returns 400 Bad Request."""
    response = api_client.get("/api/v1/titles/documentary/100/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"]["code"] == "invalid_media_type"


@pytest.mark.django_db
def test_title_detail_english_language_support(api_client):
    """Verify ?lang=en requests English metadata."""
    mock_en_movie = {
        "id": 600,
        "title": "Interstellar",
        "overview": "A team of explorers travel through a wormhole in space.",
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_movie_detail.return_value = mock_en_movie

        response = api_client.get("/api/v1/titles/movie/600/?lang=en")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title_en"] == "Interstellar"
    assert data["display_title"] == "Interstellar"
    assert "wormhole" in data["display_overview"]
