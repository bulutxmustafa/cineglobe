"""Faz 7B tests: Film Notebook (privacy, validation, lookup, stats, export, merge)."""

import csv
import io
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBNotFoundError
from apps.notebook.models import NotebookEntry
from apps.notebook.services import refresh_snapshots
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
User = get_user_model()
URL = "/api/v1/me/notebook/"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def fake_tmdb():
    client = MagicMock()

    def movie(tmdb_id, language="tr-TR"):
        if tmdb_id == 404:
            raise TMDBNotFoundError("nope")
        return {
            "title": f"Film {tmdb_id}",
            "original_title": f"Film {tmdb_id}",
            "release_date": "2010-07-16",
            "runtime": 120,
            "genres": [
                {"id": 53, "name": "Gerilim"},
                {"id": 878, "name": "Bilim Kurgu"},
            ],
            "poster_path": "/p.jpg",
        }

    def tv(tmdb_id, language="tr-TR"):
        return {
            "name": f"Dizi {tmdb_id}",
            "original_name": f"Dizi {tmdb_id}",
            "first_air_date": "2008-01-20",
            "episode_run_time": [],  # TMDB leaves this empty nowadays
            "last_episode_to_air": {"runtime": 50},
            "number_of_episodes": 62,
            "genres": [{"id": 18, "name": "Dram"}],
            "poster_path": "/s.jpg",
        }

    client.get_movie_detail.side_effect = movie
    client.get_tv_detail.side_effect = tv
    return client


@pytest.fixture(autouse=True)
def tmdb():
    client = fake_tmdb()
    with patch("apps.notebook.views.TMDBClient", return_value=client):
        yield client


def make_user(email="ada@example.com"):
    return User.objects.create_user(email=email, password="x")


@pytest.fixture
def ada():
    return make_user()


@pytest.fixture
def client(ada):
    api = APIClient()
    api.force_authenticate(ada)
    return api


def put(client, key, **body):
    return client.put(f"{URL}{key}/", body, format="json")


# ---------------------------------------------------------------------------
# Upsert, snapshot, uniqueness
# ---------------------------------------------------------------------------


def test_first_write_creates_entry_with_tmdb_snapshot(client):
    response = put(client, "movie/27205", status="watched", rating_x2=9)
    assert response.status_code == 201
    body = response.json()
    assert (body["title"], body["year"], body["genres"]) == (
        "Film 27205",
        2010,
        ["Thriller", "Science Fiction"],
    )
    assert body["watched_on"] == timezone.localdate().isoformat()  # set automatically
    again = client.patch(
        f"{URL}movie/27205/", {"note": "İkinci kez izle"}, format="json"
    )
    assert again.status_code == 200 and again.json()["rating_x2"] == 9
    assert NotebookEntry.objects.count() == 1


def test_series_snapshot_uses_last_episode_runtime(client):
    put(client, "tv/1396", status="watched")
    entry = NotebookEntry.objects.get()
    assert (entry.episode_runtime, entry.episode_count, entry.watch_minutes()) == (
        50,
        62,
        3100,
    )


def test_same_id_movie_and_series_are_separate_entries(client):
    put(client, "movie/550", status="watched")
    put(client, "tv/550", status="want_to_watch")
    assert NotebookEntry.objects.count() == 2


def test_database_enforces_one_entry_per_title(ada):
    NotebookEntry.objects.create(user=ada, media_type="movie", tmdb_id=1)
    with pytest.raises(IntegrityError):
        NotebookEntry.objects.create(user=ada, media_type="movie", tmdb_id=1)


def test_unknown_title_and_tmdb_down(client, tmdb):
    assert put(client, "movie/404", status="watched").status_code == 404
    with patch("apps.notebook.views.TMDBClient", side_effect=ValueError("no key")):
        assert put(client, "movie/1", status="watched").status_code == 503


def test_bad_media_type(client):
    assert put(client, "radio/1", status="watched").status_code == 400


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rating", [0, 11, 5.5, "abc", -1])
def test_invalid_ratings_rejected(client, rating):
    assert put(client, "movie/1", rating_x2=rating).status_code == 400
    assert not NotebookEntry.objects.exists()


@pytest.mark.parametrize("rating", [1, 10, None])
def test_valid_ratings_accepted(client, rating):
    assert put(client, "movie/1", rating_x2=rating).status_code == 201


def test_note_and_tag_limits(client):
    assert put(client, "movie/1", note="x" * 5001).status_code == 400
    assert put(client, "movie/1", tags=[f"t{i}" for i in range(11)]).status_code == 400
    assert put(client, "movie/1", tags=["x" * 31]).status_code == 400
    ok = put(client, "movie/1", note="x" * 5000, tags=["  favori ", "favori", "2026"])
    assert ok.status_code == 201 and ok.json()["tags"] == ["favori", "2026"]


def test_status_enum(client):
    assert put(client, "movie/1", status="binged").status_code == 400
    assert put(client, "movie/1", status=None).status_code == 201


def test_note_is_stored_as_plain_text(client):
    note = '<script>alert("x")</script> & <b>kalın</b>'
    body = put(client, "movie/1", note=note).json()
    assert body["note"] == note  # verbatim; the web app renders it as text, never HTML


# ---------------------------------------------------------------------------
# Privacy (IDOR)
# ---------------------------------------------------------------------------


def test_other_users_cannot_see_or_change_my_entries(client, ada):
    put(client, "movie/1", status="watched", note="özel not", rating_x2=10)
    eve = make_user("eve@example.com")
    attacker = APIClient()
    attacker.force_authenticate(eve)

    assert attacker.get(f"{URL}movie/1/").status_code == 404
    assert attacker.delete(f"{URL}movie/1/").status_code == 404
    assert attacker.get(URL).json()["total_results"] == 0
    assert (
        attacker.post(
            f"{URL}lookup/",
            {"items": [{"media_type": "movie", "tmdb_id": 1}]},
            format="json",
        ).json()
        == {}
    )
    assert attacker.get(f"{URL}stats/").json()["watched_movies"] == 0
    assert (
        "özel not"
        not in attacker.get(f"{URL}export/", {"format": "json"}).content.decode()
    )
    # Writing to the same title creates the attacker's own entry, not a change to Ada's.
    attacker.patch(f"{URL}movie/1/", {"note": "değişti"}, format="json")
    assert NotebookEntry.objects.get(user=ada).note == "özel not"


@pytest.mark.parametrize(
    "path", ["", "movie/1/", "lookup/", "stats/", "export/", "merge/"]
)
def test_notebook_requires_sign_in(path):
    response = APIClient().get(f"{URL}{path}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# List, lookup, stats
# ---------------------------------------------------------------------------


def test_list_filters_search_and_sort(client):
    put(client, "movie/1", status="watched", rating_x2=8, tags=["nolan"])
    put(client, "movie/2", status="want_to_watch", is_favorite=True)
    put(client, "tv/3", status="watched", rating_x2=10, note="müthiş final")

    def keys(**params):
        return [
            f"{r['media_type']}:{r['tmdb_id']}"
            for r in client.get(URL, params).json()["results"]
        ]

    assert keys(status="watched", sort="-rating") == ["tv:3", "movie:1"]
    assert keys(favorites=True) == ["movie:2"]
    assert keys(media_type="tv") == ["tv:3"]
    assert keys(rating_min=9) == ["tv:3"]
    assert keys(tag="nolan") == ["movie:1"]
    assert keys(genre="Drama") == ["tv:3"]
    assert keys(q="müthiş") == ["tv:3"]
    assert client.get(URL, {"sort": "random"}).status_code == 400


def test_lookup_is_one_query_and_ignores_unknown_ids(client, django_assert_num_queries):
    put(client, "movie/1", status="watched", rating_x2=9)
    put(client, "tv/1", is_favorite=True)
    items = [
        {"media_type": "movie", "tmdb_id": 1},
        {"media_type": "movie", "tmdb_id": 999},
        {"media_type": "tv", "tmdb_id": 1},
    ]
    from apps.notebook.services import lookup

    user = User.objects.get()
    with django_assert_num_queries(1):
        result = lookup(user, [(i["media_type"], i["tmdb_id"]) for i in items])
    assert result == {
        "movie:1": {"status": "watched", "is_favorite": False, "rating_x2": 9},
        "tv:1": {"status": None, "is_favorite": True, "rating_x2": None},
    }
    assert (
        client.post(f"{URL}lookup/", {"items": items}, format="json").json() == result
    )


def test_stats_match_known_fixture(ada):
    today = date(2026, 10, 9)

    def entry(tmdb_id, media_type="movie", **kw):
        return NotebookEntry.objects.create(
            user=ada, media_type=media_type, tmdb_id=tmdb_id, **kw
        )

    entry(
        1,
        status="watched",
        rating_x2=10,
        runtime_minutes=120,
        genres=["Thriller"],
        watched_on=today,
        title="A",
    )
    entry(
        2,
        status="watched",
        rating_x2=6,
        runtime_minutes=90,
        rewatch_count=1,
        genres=["Thriller", "Drama"],
        watched_on=date(2025, 3, 1),
        title="B",
    )
    entry(
        3,
        "tv",
        status="watched",
        rating_x2=8,
        episode_runtime=50,
        episode_count=10,
        genres=["Drama"],
        watched_on=today,
        title="C",
    )
    entry(4, status="want_to_watch", is_favorite=True)
    stats = APIClient()
    stats.force_authenticate(ada)
    body = stats.get(f"{URL}stats/").json()
    assert (
        body["watched_movies"],
        body["watched_series"],
        body["want_to_watch"],
        body["favorites"],
    ) == (2, 1, 1, 1)
    assert body["total_watch_minutes"] == 120 + 90 * 2 + 50 * 10
    assert body["average_rating"] == 4.0  # (10 + 6 + 8) / 3 / 2
    assert (
        body["rating_distribution"]["10"] == 1 and body["rating_distribution"]["1"] == 0
    )
    assert body["genre_distribution"] == {"Thriller": 2, "Drama": 2}
    assert body["watched_by_month"] == {"2025-03": 1, "2026-10": 2}
    assert body["watched_by_year"] == {"2025": 1, "2026": 2}
    assert [t["title"] for t in body["top_rated"]] == ["A", "C", "B"]


# ---------------------------------------------------------------------------
# Export, merge, account deletion
# ---------------------------------------------------------------------------


def test_export_csv_and_json(client):
    put(
        client,
        "movie/1",
        status="watched",
        rating_x2=9,
        tags=["a", "b"],
        note="çok iyi",
    )
    csv_response = client.get(f"{URL}export/", {"format": "csv"})
    assert csv_response["Content-Type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(csv_response.content.decode("utf-8-sig"))))
    assert (
        rows[0]["rating"] == "4.5"
        and rows[0]["tags"] == "a|b"
        and rows[0]["note"] == "çok iyi"
    )
    data = json.loads(client.get(f"{URL}export/", {"format": "json"}).content)
    assert data[0]["status"] == "watched"
    assert client.get(f"{URL}export/", {"format": "xml"}).status_code == 400


def test_account_export_includes_notebook(client):
    put(client, "movie/1", status="watched")
    data = json.loads(client.get("/api/v1/me/export/").content)
    assert data["notebook"][0]["tmdb_id"] == 1


def test_merge_guest_favorites_account_wins(client, ada):
    put(client, "movie/1", is_favorite=False, status="dropped")
    response = client.post(
        f"{URL}merge/",
        {
            "favorites": [
                {"media_type": "movie", "tmdb_id": 1},
                {"media_type": "movie", "tmdb_id": 2},
                {"media_type": "movie", "tmdb_id": 404},
            ]
        },
        format="json",
    )
    assert response.json() == {"added": 1, "skipped": 2}
    assert (
        NotebookEntry.objects.get(tmdb_id=1).is_favorite is False
    )  # account data kept
    assert NotebookEntry.objects.get(tmdb_id=2).is_favorite is True


def test_deleting_account_deletes_notebook(ada):
    NotebookEntry.objects.create(user=ada, media_type="movie", tmdb_id=1)
    ada.delete()
    assert not NotebookEntry.objects.exists()


# ---------------------------------------------------------------------------
# Watched filter (search, collections, Lucky Globe)
# ---------------------------------------------------------------------------


def test_exclude_watched_in_collections_keeps_want_to_watch(client, ada):
    NotebookEntry.objects.create(
        user=ada, media_type="movie", tmdb_id=1, status="watched"
    )
    NotebookEntry.objects.create(
        user=ada, media_type="movie", tmdb_id=2, status="want_to_watch"
    )
    items = [{"media_type": "movie", "tmdb_id": i, "title": f"M{i}"} for i in (1, 2, 3)]
    with patch("apps.collections.views.RecipeEngine") as engine:
        engine.return_value.items.return_value = items
        engine.return_value.random_pick.side_effect = (
            lambda collection, media, lang, exclude: exclude
        )
        body = client.get(
            "/api/v1/collections/snack-watch/",
            {"exclude_watched": "true", "lang": "tr"},
        )
        assert [r["tmdb_id"] for r in body.json()["results"]] == [2, 3]
        assert (
            body["Cache-Control"] == "private, no-store"
        )  # personal: never CDN-shared
        excluded = client.get(
            "/api/v1/collections/snack-watch/random/", {"exclude_watched": "true"}
        ).json()["pick"]
        assert set(excluded) == {"movie:1"}


def test_exclude_watched_in_search(client, ada):
    NotebookEntry.objects.create(
        user=ada, media_type="movie", tmdb_id=1, status="watched"
    )
    payload = {
        "ai_status": "fallback",
        "count": 2,
        "results": [
            {"media_type": "movie", "tmdb_id": 1},
            {"media_type": "tv", "tmdb_id": 1},
        ],
    }
    with patch("apps.search.views.SearchService") as service:
        service.return_value.search.return_value = payload
        body = client.post(
            "/api/v1/search/",
            {"query": "gerilim", "exclude_watched": True},
            format="json",
        ).json()
    assert [(r["media_type"], r["tmdb_id"]) for r in body["results"]] == [("tv", 1)]


def test_notes_never_reach_the_llm(client, ada):
    from apps.search.providers.classic import ClassicProvider
    from apps.search.schemas import SearchFilters
    from search_fakes import FakeProvider, tmdb_item
    from search_fakes import fake_tmdb as fake_search_tmdb

    NotebookEntry.objects.create(
        user=ada, media_type="movie", tmdb_id=1, note="GİZLİ-NOT-123", rating_x2=10
    )
    llm = FakeProvider("gemini", SearchFilters(genres_include=["Action"]))
    with (
        patch("apps.search.router.build_chain", return_value=[llm, ClassicProvider()]),
        patch(
            "apps.search.service.TMDBClient",
            return_value=fake_search_tmdb(movies=[tmdb_item(1, genre_ids=[28])]),
        ),
    ):
        client.post("/api/v1/search/", {"query": "aksiyon"}, format="json")
    assert llm.parse_calls and "GİZLİ-NOT-123" not in repr(llm.received)


# ---------------------------------------------------------------------------
# Snapshot refresh (TMDB 6-month rule)
# ---------------------------------------------------------------------------


def test_snapshot_refresh_and_six_month_clearing(ada):
    now = timezone.now()
    fresh = NotebookEntry.objects.create(
        user=ada,
        media_type="movie",
        tmdb_id=1,
        title="Eski ad",
        snapshot_at=now - timedelta(days=40),
    )
    expired = NotebookEntry.objects.create(
        user=ada,
        media_type="movie",
        tmdb_id=404,
        title="Silinmiş film",
        poster_path="/x.jpg",
        status="watched",
        rating_x2=8,
        note="kendi notum",
        snapshot_at=now - timedelta(days=200),
    )
    result = refresh_snapshots(fake_tmdb())
    fresh.refresh_from_db()
    expired.refresh_from_db()
    assert result == {"refreshed": 1, "cleared": 1}
    assert fresh.title == "Film 1"
    assert (expired.title, expired.poster_path, expired.snapshot_at) == ("", "", None)
    assert (expired.status, expired.rating_x2, expired.note) == (
        "watched",
        8,
        "kendi notum",
    )
