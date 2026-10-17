"""Search-friendly guides: list, one guide with titles, unknown slug."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.guides import GUIDES, GUIDES_BY_SLUG
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def item(tmdb_id, poster="/p.jpg", genres=(53,)):
    return {
        "id": tmdb_id,
        "title": f"T{tmdb_id}",
        "poster_path": poster,
        "genre_ids": list(genres),
        "vote_average": 8.0,
        "vote_count": 5000,
        "popularity": 10.0,
    }


def test_guides_have_unique_slugs_and_both_languages():
    assert len(GUIDES_BY_SLUG) == len(GUIDES)
    for guide in GUIDES:
        assert guide.media_type in ("movie", "tv")
        assert guide.title_tr and guide.title_en and guide.intro_tr and guide.intro_en


def test_recent_guide_limits_release_year():
    params = GUIDES_BY_SLUG["bu-aksam-ne-izlesem"].discover_params(date(2026, 5, 1))
    assert params["primary_release_date.gte"] == "2023-01-01"


def test_guide_list_with_card_posters(api_client):
    client = MagicMock()
    client.discover_movies.return_value = {"results": [item(1), item(2, poster=None)]}
    client.discover_tv.return_value = {"results": [item(5)]}
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        data = api_client.get("/api/v1/guides/", {"lang": "en"}).json()
    assert [g["slug"] for g in data["guides"]] == [g.slug for g in GUIDES]
    assert data["guides"][1]["title"] == "Best thriller films"
    assert len(data["guides"][1]["posters"]) == 1


def test_guide_detail_filters_posterless_and_talk_shows(api_client):
    client = MagicMock()
    client.discover_movies.side_effect = lambda params, language: {
        "results": (
            [item(1), item(2, poster=None), item(3, genres=(10767,))]
            if params["page"] == 1
            else []
        )
    }
    with patch("apps.catalog.views.TMDBClient", return_value=client):
        response = api_client.get(
            "/api/v1/guides/en-iyi-gerilim-filmleri/", {"lang": "tr"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["guide"]["title"] == "En iyi gerilim filmleri"
    assert [r["tmdb_id"] for r in body["results"]] == [1]
    sent = client.discover_movies.call_args_list[0].args[0]
    assert sent["with_genres"] == "53" and sent["sort_by"] == "vote_average.desc"


def test_unknown_guide_is_404(api_client):
    assert api_client.get("/api/v1/guides/yok-boyle-bir-liste/").status_code == 404
