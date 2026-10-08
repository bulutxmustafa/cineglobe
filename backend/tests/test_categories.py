"""Tests for Curated & Mood-based categories endpoints."""

from unittest.mock import patch

from apps.catalog.categories import CURATED_CATEGORIES, get_curated_category
from apps.catalog.tmdb_client import TMDBServiceUnavailableError
from rest_framework import status


def test_category_definitions_integrity():
    """Verify curated categories are properly configured."""
    assert len(CURATED_CATEGORIES) >= 6
    required_slugs = [
        "sikilmam-diyeceginiz",
        "surukleyici",
        "cerezlik",
        "kafanizi-dagitacak",
        "basladigi-gibi-bitecek",
        "terskose",
    ]
    for slug in required_slugs:
        cat = get_curated_category(slug)
        assert cat is not None
        assert cat.title_tr
        assert cat.title_en
        assert cat.icon


def test_list_curated_categories(api_client):
    """Verify GET /api/v1/categories/ returns all categories in requested language."""
    # Turkish
    resp_tr = api_client.get("/api/v1/categories/?lang=tr")
    assert resp_tr.status_code == status.HTTP_200_OK
    data_tr = resp_tr.json()
    assert data_tr["count"] >= 6
    assert any(
        c["slug"] == "terskose" and "Tersköşe" in c["title"]
        for c in data_tr["categories"]
    )

    # English
    resp_en = api_client.get("/api/v1/categories/?lang=en")
    assert resp_en.status_code == status.HTTP_200_OK
    data_en = resp_en.json()
    assert any(
        c["slug"] == "terskose" and "Twist" in c["title"] for c in data_en["categories"]
    )


def test_get_curated_category_detail(api_client):
    """Verify GET /api/v1/categories/{slug}/ fetches and formats movies & series."""
    mock_movie_results = {
        "results": [
            {
                "id": 101,
                "title": "Mementö",
                "vote_average": 8.4,
                "popularity": 45.0,
                "poster_path": "/memento.jpg",
                "backdrop_path": "/memento_bg.jpg",
                "release_date": "2000-10-11",
            }
        ]
    }
    mock_tv_results = {
        "results": [
            {
                "id": 202,
                "name": "Dark",
                "vote_average": 8.7,
                "popularity": 60.0,
                "poster_path": "/dark.jpg",
                "backdrop_path": "/dark_bg.jpg",
                "first_air_date": "2017-12-01",
            }
        ]
    }

    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.discover_movies.return_value = mock_movie_results
        mock_instance.discover_tv.return_value = mock_tv_results

        resp = api_client.get("/api/v1/categories/terskose/")

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["category"]["slug"] == "terskose"
    assert data["count"] == 2
    # Verify both movie and TV titles are cleanly unified
    assert any(
        item["tmdb_id"] == 101 and item["media_type"] == "movie"
        for item in data["results"]
    )
    assert any(
        item["tmdb_id"] == 202 and item["media_type"] == "tv"
        for item in data["results"]
    )


def test_get_curated_category_not_found(api_client):
    """Verify non-existent category slug returns 404."""
    resp = api_client.get("/api/v1/categories/non-existent-category/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["error"]["code"] == "category_not_found"


def test_curated_category_tmdb_error_returns_503(api_client):
    """Verify TMDB error returns 503."""
    with patch("apps.catalog.views.TMDBClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.discover_movies.side_effect = TMDBServiceUnavailableError("Down")

        resp = api_client.get("/api/v1/categories/surukleyici/")

    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
