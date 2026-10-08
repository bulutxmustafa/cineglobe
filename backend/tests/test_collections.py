"""Faz 4B tests: curated collections (recipe, engine, endpoints, admin, cache)."""

import random
import time
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from apps.collections.engine import RecipeEngine, build_discover_params
from apps.collections.models import Collection
from apps.collections.recipe import Recipe
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status

pytestmark = pytest.mark.django_db

APPROVED = [
    "never-boring",
    "immersive",
    "snack-watch",
    "switch-off",
    "start-to-finish",
    "curveball",
]


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def movie(tmdb_id, *, genres=(35,), rating=7.5, votes=5000, adult=False, title=None):
    return {
        "id": tmdb_id,
        "title": title or f"Movie {tmdb_id}",
        "release_date": "2010-01-01",
        "overview": "x",
        "poster_path": "/p.jpg",
        "backdrop_path": "/b.jpg",
        "vote_average": rating,
        "vote_count": votes,
        "popularity": 10.0,
        "genre_ids": list(genres),
        "adult": adult,
    }


def fake_tmdb(pages=None, tv_pages=None):
    """discover_* return the given pages in order (each page is a list of items)."""
    client = MagicMock()
    pages = pages if pages is not None else [[movie(i) for i in range(1, 21)]]
    tv_pages = tv_pages or [[]]

    def paged(source):
        def discover(params, language="tr-TR"):
            index = params.get("page", 1) - 1
            results = source[index] if index < len(source) else []
            return {"results": results, "total_pages": len(source)}

        return discover

    client.discover_movies.side_effect = paged(pages)
    client.discover_tv.side_effect = paged(tv_pages)
    client.search_keyword.side_effect = lambda q: {
        "results": [{"id": 9000 + len(q), "name": q}]
    }

    def detail(tmdb_id, language="tr-TR"):
        if tmdb_id == 404:
            raise TMDBNotFoundError("gone")
        return {
            "id": tmdb_id,
            "title": f"Pinned {tmdb_id}",
            "name": f"Pinned {tmdb_id}",
            "genres": [{"id": 18, "name": "Drama"}],
            "vote_average": 8.0,
            "vote_count": 100,
            "release_date": "2000-01-01",
        }

    client.get_movie_detail.side_effect = detail
    client.get_tv_detail.side_effect = detail
    return client


def make(slug="test-col", recipe=None, **kw):
    return Collection.objects.create(
        slug=slug,
        name_tr="Test TR",
        name_en="Test EN",
        description_tr="Açıklama",
        description_en="Description",
        reason_tr="Neden TR",
        reason_en="Why EN",
        icon="🎬",
        recipe=recipe if recipe is not None else {"genres": ["Comedy"]},
        **kw,
    )


@pytest.fixture
def tmdb():
    client = fake_tmdb()
    with patch("apps.collections.views.TMDBClient", return_value=client):
        yield client


# ---------------------------------------------------------------------------
# Recipe validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "recipe",
    [
        {"genres": ["Telenovela"]},
        {"genres": ["Comedy"], "genres_exclude": ["Comedy"]},
        {"runtime_min": 120, "runtime_max": 90},
        {"min_rating": 11},
        {"pages": 9},
        {"min_votes": -1},
        {"unknown_field": 1},
    ],
)
def test_invalid_recipes_are_rejected(recipe):
    with pytest.raises(PydanticValidationError):
        Recipe.model_validate(recipe)
    with pytest.raises(ValidationError):
        make(recipe=recipe).full_clean()


def test_pin_and_blocklist_formats_are_validated():
    with pytest.raises(ValidationError):
        make(editor_pins=["550"]).full_clean()
    make(slug="ok", editor_pins=["movie:550", "tv:1396"]).full_clean()


def test_keywords_are_normalised():
    assert Recipe(keywords=["  Plot   Twist ", "plot twist"]).keywords == ["plot twist"]


# ---------------------------------------------------------------------------
# Recipe → TMDB discover params
# ---------------------------------------------------------------------------


def test_discover_params_movie():
    recipe = Recipe(
        genres=["Comedy", "Family"],
        genres_exclude=["Horror"],
        runtime_min=80,
        runtime_max=110,
        min_rating=6.5,
        min_votes=1500,
        vote_count_max=9000,
        year_from=1990,
        year_to=1999,
    )
    params = build_discover_params(recipe, "movie", [1, 2])
    assert params == {
        "include_adult": "false",
        "vote_count.gte": 1500,
        "sort_by": "vote_average.desc",
        "with_genres": "35|10751",
        "without_genres": "27",
        "with_keywords": "1|2",
        "vote_average.gte": 6.5,
        "vote_count.lte": 9000,
        "primary_release_date.gte": "1990-01-01",
        "primary_release_date.lte": "1999-12-31",
        "with_runtime.gte": 80,
        "with_runtime.lte": 110,
    }


def test_discover_params_tv_uses_stand_ins_and_series_filters():
    recipe = Recipe(
        genres=["Thriller"], episode_runtime_max=30, status="ended", sort_by="newest"
    )
    params = build_discover_params(recipe, "tv", [])
    assert params["with_genres"] == "9648|80"
    assert params["with_runtime.lte"] == 30
    assert params["with_status"] == "3|4"
    assert params["sort_by"] == "first_air_date.desc"


def test_recipe_without_any_genre_for_media_type_is_skipped():
    assert build_discover_params(Recipe(genres=["TV Movie"]), "tv", []) is None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def test_genres_exclude_is_a_hard_filter():
    # TMDB may still return a horror-tagged title; the engine must drop it.
    client = fake_tmdb([[movie(1, genres=(35,)), movie(2, genres=(35, 27))]])
    collection = make(
        recipe={"genres": ["Comedy"], "genres_exclude": ["Horror"], "pages": 1}
    )
    items = RecipeEngine(client).items(collection, "both", "tr")
    assert [i["tmdb_id"] for i in items] == [1]


def test_snack_watch_never_contains_horror(tmdb):
    tmdb.discover_movies.side_effect = lambda p, language="tr-TR": {
        "results": [movie(1, genres=(35,)), movie(2, genres=(35, 27))],
        "total_pages": 1,
    }
    body = tmdb_get("/api/v1/collections/snack-watch/")
    assert all(27 not in r["genre_ids"] for r in body["results"])
    assert "27" in tmdb.discover_movies.call_args.args[0]["without_genres"]


def test_pins_first_blocklist_removed_adult_dropped():
    client = fake_tmdb([[movie(1), movie(2), movie(3, adult=True)]])
    collection = make(
        recipe={"genres": ["Comedy"], "pages": 1},
        editor_pins=["movie:77", "movie:404", "movie:2"],
        editor_blocklist=["movie:1"],
    )
    items = RecipeEngine(client).items(collection, "both", "tr")
    assert [(i["tmdb_id"], i["pinned"]) for i in items] == [(77, True), (2, True)]


def test_ranking_uses_vote_confidence():
    client = fake_tmdb(
        [[movie(1, rating=9.9, votes=20), movie(2, rating=8.0, votes=30000)]]
    )
    items = RecipeEngine(client).items(make(recipe={"pages": 1}), "both", "tr")
    assert [i["tmdb_id"] for i in items] == [2, 1]


def test_reason_and_language_follow_request():
    client = fake_tmdb()
    collection = make()
    tr = RecipeEngine(client).items(collection, "both", "tr")
    en = RecipeEngine(client).items(collection, "both", "en")
    assert tr[0]["reason"] == "Neden TR" and en[0]["reason"] == "Why EN"
    languages = {c.kwargs["language"] for c in client.discover_movies.call_args_list}
    assert languages == {"tr", "en"}


def test_fetches_recipe_pages_and_stops_at_last_page():
    client = fake_tmdb(
        [[movie(i) for i in range(1, 21)], [movie(i) for i in range(21, 31)]]
    )
    items = RecipeEngine(client).items(make(recipe={"pages": 5}), "both", "tr")
    assert len(items) == 30
    assert client.discover_movies.call_count == 2


def test_movie_only_collection_ignores_tv_request():
    client = fake_tmdb()
    assert RecipeEngine(client).items(make(), "tv", "tr") == []
    client.discover_tv.assert_not_called()


def test_both_collection_queries_movies_and_series():
    client = fake_tmdb([[movie(1)]], tv_pages=[[{**movie(1), "name": "Show 1"}]])
    items = RecipeEngine(client).items(make(media_type="both"), "both", "tr")
    assert {(i["media_type"], i["tmdb_id"]) for i in items} == {("movie", 1), ("tv", 1)}


def test_cache_is_used_and_invalidated_by_admin_edit():
    client = fake_tmdb()
    collection = make()
    engine = RecipeEngine(client)
    engine.items(collection, "both", "tr")
    engine.items(collection, "both", "tr")
    assert client.discover_movies.call_count == 1  # second call served from cache

    collection.editor_blocklist = ["movie:1"]
    collection.save()  # updated_at changes → new cache key
    items = engine.items(Collection.objects.get(pk=collection.pk), "both", "tr")
    assert "movie:1" not in {f"{i['media_type']}:{i['tmdb_id']}" for i in items}
    assert client.discover_movies.call_count == 2


def test_cached_page_is_fast():
    collection = make()
    engine = RecipeEngine(fake_tmdb())
    engine.items(collection, "both", "tr")
    started = time.monotonic()
    engine.page(collection, "both", "tr", 1)
    assert (time.monotonic() - started) < 0.3


def test_random_pick_avoids_recent_picks_and_falls_back_when_all_excluded():
    client = fake_tmdb([[movie(1), movie(2), movie(3)]])
    collection = make(recipe={"pages": 1})
    engine = RecipeEngine(client)
    rng = random.Random(7)
    picks = {
        engine.random_pick(collection, "both", "tr", {"movie:1", "movie:2"}, rng)[
            "tmdb_id"
        ]
        for _ in range(10)
    }
    assert picks == {3}
    every = {"movie:1", "movie:2", "movie:3"}
    assert engine.random_pick(collection, "both", "tr", every, rng) is not None


def test_empty_collection():
    engine = RecipeEngine(fake_tmdb([[]]))
    collection = make()
    assert engine.page(collection, "both", "tr", 1) == {
        "page": 1,
        "total_pages": 1,
        "total_results": 0,
        "results": [],
    }
    assert engine.random_pick(collection, "both", "tr", set()) is None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def tmdb_get(url, **params):
    from rest_framework.test import APIClient

    response = APIClient().get(url, params)
    assert response.status_code == 200, response.content
    return response.json()


def test_approved_collections_are_seeded_in_order(api_client):
    body = api_client.get("/api/v1/collections/", {"lang": "tr"}).json()
    assert [c["slug"] for c in body["collections"]] == APPROVED
    assert body["collections"][0]["name"] == "Sıkılmam Diyeceğiniz Filmler"


def test_list_in_english_and_hides_inactive(api_client):
    Collection.objects.filter(slug="curveball").update(is_active=False)
    body = api_client.get("/api/v1/collections/", {"lang": "en"}).json()
    assert "curveball" not in [c["slug"] for c in body["collections"]]
    assert body["collections"][0]["name"] == "Films You Won't Get Bored Of"


def test_detail_paginates(tmdb):
    tmdb.discover_movies.side_effect = lambda p, language="tr-TR": {
        "results": [movie(i + 100 * p["page"]) for i in range(20)],
        "total_pages": 3,
    }
    first = tmdb_get("/api/v1/collections/never-boring/", lang="tr")
    third = tmdb_get("/api/v1/collections/never-boring/", lang="tr", page=3)
    assert (first["total_results"], first["total_pages"]) == (60, 3)
    assert len(first["results"]) == 20 and len(third["results"]) == 20
    assert first["collection"]["slug"] == "never-boring"
    assert first["results"][0]["reason"]


def test_unknown_or_inactive_collection_is_404(api_client, tmdb):
    assert api_client.get("/api/v1/collections/nope/").status_code == 404
    Collection.objects.filter(slug="curveball").update(is_active=False)
    assert api_client.get("/api/v1/collections/curveball/").status_code == 404


def test_tmdb_down_is_503(api_client, tmdb):
    tmdb.discover_movies.side_effect = TMDBServiceUnavailableError("down")
    response = api_client.get("/api/v1/collections/snack-watch/", {"lang": "en"})
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["error"]["code"] == "service_unavailable"


def test_missing_tmdb_key_is_503(api_client, settings):
    settings.TMDB_API_KEY = ""
    assert api_client.get("/api/v1/collections/snack-watch/").status_code == 503


def test_random_endpoint(api_client, tmdb):
    body = api_client.get(
        "/api/v1/collections/snack-watch/random/", {"exclude": "movie:1,movie:2"}
    ).json()
    assert body["pick"]["tmdb_id"] not in (1, 2)
    assert body["collection"]["slug"] == "snack-watch"


def test_cdn_cache_headers_only_with_explicit_lang(api_client, tmdb):
    with_lang = api_client.get("/api/v1/collections/snack-watch/", {"lang": "tr"})
    assert "s-maxage=3600" in with_lang["Cache-Control"]
    assert "Accept-Language" in with_lang["Vary"]
    assert "Cookie" not in with_lang["Vary"]  # shareable by the CDN
    header_lang = api_client.get("/api/v1/collections/snack-watch/")
    assert header_lang["Cache-Control"] == "private, max-age=0"
    random_pick = api_client.get(
        "/api/v1/collections/snack-watch/random/", {"lang": "tr"}
    )
    assert "s-maxage" not in random_pick.get("Cache-Control", "")


def test_bad_media_type_is_400(api_client, tmdb):
    response = api_client.get(
        "/api/v1/collections/snack-watch/", {"media_type": "radio"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Admin (editors work without code changes)
# ---------------------------------------------------------------------------


def test_admin_can_add_collection_and_rejects_bad_recipe(client):
    admin = get_user_model().objects.create_superuser(
        "root", "r@example.com", "pw-123456"
    )
    client.force_login(admin)
    form = {
        "slug": "date-night",
        "icon": "💞",
        "media_type": "movie",
        "is_active": "on",
        "sort_order": "7",
        "name_tr": "Randevu Gecesi",
        "description_tr": "",
        "reason_tr": "",
        "name_en": "Date Night",
        "description_en": "",
        "reason_en": "",
        "recipe": '{"genres": ["Romance", "Comedy"]}',
        "editor_pins": "[]",
        "editor_blocklist": "[]",
    }
    response = client.post("/admin/collections/collection/add/", form)
    assert response.status_code == 302
    assert Collection.objects.get(slug="date-night").name_en == "Date Night"

    bad = {**form, "slug": "broken", "recipe": '{"genres": ["Telenovela"]}'}
    response = client.post("/admin/collections/collection/add/", bad)
    assert response.status_code == 200 and b"Invalid recipe" in response.content
    assert not Collection.objects.filter(slug="broken").exists()
    assert client.get("/admin/collections/collection/").status_code == 200
