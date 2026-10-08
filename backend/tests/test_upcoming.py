"""Faz 4C tests: upcoming releases (grouping, Istanbul date, TR/global, sources)."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBServiceUnavailableError
from apps.upcoming.service import UpcomingService, group_for
from django.core.cache import cache
from rest_framework import status

TODAY = date(2026, 10, 8)  # a Thursday


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _today():
    with patch("apps.upcoming.service.local_today", return_value=TODAY):
        yield


def m(tmdb_id, release, *, popularity=20.0, genres=(28,), adult=False):
    return {
        "id": tmdb_id,
        "title": f"Movie {tmdb_id}",
        "original_title": f"Movie {tmdb_id}",
        "release_date": release,
        "popularity": popularity,
        "genre_ids": list(genres),
        "adult": adult,
    }


def s(tmdb_id, first_air, *, popularity=20.0, genres=(18,)):
    return {
        "id": tmdb_id,
        "name": f"Show {tmdb_id}",
        "original_name": f"Show {tmdb_id}",
        "first_air_date": first_air,
        "popularity": popularity,
        "genre_ids": list(genres),
    }


def fake(tr=(), global_movies=(), premieres=(), returning=(), details=None):
    """TMDB double routing discover calls by their parameters."""
    client = MagicMock()

    def discover_movies(params, language="tr-TR"):
        source = tr if "region" in params else global_movies
        return {
            "results": list(source) if params["page"] == 1 else [],
            "total_pages": 1,
        }

    def discover_tv(params, language="tr-TR"):
        source = returning if "air_date.gte" in params else premieres
        return {
            "results": list(source) if params["page"] == 1 else [],
            "total_pages": 1,
        }

    client.discover_movies.side_effect = discover_movies
    client.discover_tv.side_effect = discover_tv
    client.get_tv_detail.side_effect = lambda tmdb_id, language="tr-TR": (
        details or {}
    )[tmdb_id]
    return client


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "release, group",
    [
        ("2026-10-08", "this_week"),  # today
        ("2026-10-09", "this_week"),  # tomorrow
        ("2026-10-14", "this_week"),  # today + 6
        ("2026-10-15", "this_month"),  # one week out, same month
        ("2026-10-31", "this_month"),  # month end
        ("2026-11-01", "later"),  # next month
        ("", "tba"),
    ],
)
def test_group_boundaries(release, group):
    assert group_for(release, TODAY) == group


def test_week_crossing_month_end_stays_this_week():
    assert group_for("2026-11-02", date(2026, 10, 28)) == "this_week"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def test_turkish_date_wins_over_global_and_global_fills_gaps():
    client = fake(
        tr=[m(1, "2026-12-18")],
        global_movies=[m(1, "2026-12-16"), m(2, "2026-11-20")],
    )
    items = {i["tmdb_id"]: i for i in UpcomingService(client).items("tr", TODAY)}
    assert (items[1]["release_date"], items[1]["region"]) == ("2026-12-18", "TR")
    assert (items[2]["release_date"], items[2]["region"]) == ("2026-11-20", "global")


def test_only_today_or_later_is_listed():
    client = fake(tr=[m(1, "2026-10-07"), m(2, "2026-10-08"), m(3, "2026-10-09")])
    ids = [i["tmdb_id"] for i in UpcomingService(client).items("tr", TODAY)]
    assert ids == [2, 3]


def test_undated_titles_are_kept_last_in_tba_group():
    client = fake(premieres=[s(10, ""), s(11, "2026-10-20")])
    items = UpcomingService(client).items("tr", TODAY)
    assert [(i["tmdb_id"], i["group"], i["date_precision"]) for i in items] == [
        (11, "this_month", "day"),
        (10, "tba", "unknown"),
    ]
    assert items[-1]["region"] == ""


def test_returning_series_need_a_season_premiere():
    client = fake(
        returning=[s(20, "2008-01-20"), s(21, "2010-01-01"), s(22, "2012-01-01")],
        details={
            20: {
                "next_episode_to_air": {
                    "air_date": "2026-11-05",
                    "season_number": 6,
                    "episode_number": 1,
                }
            },
            21: {
                "next_episode_to_air": {
                    "air_date": "2026-10-10",
                    "season_number": 3,
                    "episode_number": 5,
                }
            },
            22: {"next_episode_to_air": None},
        },
    )
    items = UpcomingService(client).items("tr", TODAY)
    assert [(i["tmdb_id"], i["release_date"], i["season_number"]) for i in items] == [
        (20, "2026-11-05", 6)
    ]
    params = [c.args[0] for c in client.discover_tv.call_args_list]
    assert all(
        p["without_genres"] == "10767,10763,10764" for p in params
    )  # no talk shows


def test_low_popularity_global_titles_are_hidden_but_turkish_releases_kept(settings):
    settings.UPCOMING_MIN_POPULARITY = 8.0
    client = fake(
        tr=[m(1, "2026-11-01", popularity=1.0)],
        global_movies=[
            m(2, "2026-11-01", popularity=2.0),
            m(3, "2026-11-01", popularity=9.0),
        ],
        premieres=[s(4, "2026-11-01", popularity=3.0)],
    )
    ids = {
        (i["media_type"], i["tmdb_id"])
        for i in UpcomingService(client).items("tr", TODAY)
    }
    assert ids == {("movie", 1), ("movie", 3)}


def test_same_tmdb_id_movie_and_series_do_not_collide():
    client = fake(tr=[m(550, "2026-11-01")], premieres=[s(550, "2026-11-02")])
    keys = {
        (i["media_type"], i["tmdb_id"])
        for i in UpcomingService(client).items("tr", TODAY)
    }
    assert keys == {("movie", 550), ("tv", 550)}


def test_adult_titles_dropped():
    client = fake(tr=[m(1, "2026-11-01", adult=True)])
    assert UpcomingService(client).items("tr", TODAY) == []


def test_results_cached_per_local_day():
    client = fake(tr=[m(1, "2026-11-01")])
    service = UpcomingService(client)
    service.items("tr", TODAY)
    service.items("tr", TODAY)
    assert client.discover_movies.call_count == 2  # TR + global, once
    service.items("tr", date(2026, 10, 9))
    assert client.discover_movies.call_count == 4  # new day, new list


def test_page_filters_and_groups():
    client = fake(
        tr=[m(1, "2026-10-09", genres=(35,)), m(2, "2026-11-03", genres=(27,))],
        premieres=[s(3, "2026-10-12")],
    )
    service = UpcomingService(client)
    both = service.page(media_type="both", language="tr", page=1)
    assert both["today"] == "2026-10-08"
    assert [g["key"] for g in both["groups"]] == ["this_week", "later"]
    assert [
        i["tmdb_id"]
        for i in service.page(media_type="tv", language="tr", page=1)["results"]
    ] == [3]
    comedy = service.page(media_type="both", language="tr", page=1, genre="Comedy")
    assert [i["tmdb_id"] for i in comedy["results"]] == [1]
    november = service.page(media_type="both", language="tr", page=1, month="2026-11")
    assert [i["tmdb_id"] for i in november["results"]] == [2]


def test_pagination():
    client = fake(tr=[m(i, f"2026-11-{(i % 28) + 1:02d}") for i in range(1, 46)])
    service = UpcomingService(client)
    first = service.page(media_type="both", language="tr", page=1)
    third = service.page(media_type="both", language="tr", page=3)
    assert (first["total_results"], first["total_pages"]) == (45, 3)
    assert len(third["results"]) == 5


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@pytest.fixture
def endpoint_tmdb():
    client = fake(tr=[m(1, "2026-10-09")])
    with patch("apps.upcoming.views.TMDBClient", return_value=client):
        yield client


def test_endpoint(api_client, endpoint_tmdb):
    response = api_client.get("/api/v1/upcoming/", {"lang": "tr"})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"][0]["group"] == "this_week"
    assert "s-maxage=1800" in response["Cache-Control"]


@pytest.mark.parametrize(
    "params", [{"genre": "Telenovela"}, {"month": "2026-13"}, {"media_type": "radio"}]
)
def test_endpoint_rejects_bad_filters(api_client, endpoint_tmdb, params):
    assert api_client.get("/api/v1/upcoming/", params).status_code == 400


def test_endpoint_tmdb_down_is_503(api_client, endpoint_tmdb):
    endpoint_tmdb.discover_movies.side_effect = TMDBServiceUnavailableError("down")
    response = api_client.get("/api/v1/upcoming/", {"lang": "en"})
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_endpoint_missing_key_is_503(api_client, settings):
    settings.TMDB_API_KEY = ""
    assert api_client.get("/api/v1/upcoming/").status_code == 503
