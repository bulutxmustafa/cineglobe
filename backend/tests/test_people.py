"""Faz 4 tests: person resolution, best titles, filmography and detail.

Fixtures mirror the live TMDB combined_credits shape (checked 2026-10-08): TV
cast credits have no `order`, titles repeat once per character, and
self-appearances are common.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from apps.people.credits import (
    is_lead,
    is_noise,
    merge_credits,
    sort_credits,
    split_upcoming,
)
from apps.people.resolver import PersonResolver
from apps.people.services import title_reason
from django.core.cache import cache
from rest_framework import status

TODAY = date(2026, 10, 8)
FUTURE = (TODAY + timedelta(days=120)).isoformat()


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _fixed_today():
    with patch("apps.people.services.local_today", return_value=TODAY):
        yield


def movie(
    tmdb_id, title, date_, *, order=0, votes=5000, rating=7.5, character="Hero", **kw
):
    return {
        "media_type": "movie",
        "id": tmdb_id,
        "title": title,
        "original_title": title,
        "release_date": date_,
        "order": order,
        "vote_count": votes,
        "vote_average": rating,
        "popularity": kw.pop("popularity", 10.0),
        "character": character,
        "genre_ids": kw.pop("genre_ids", [18]),
        "poster_path": "/p.jpg",
        "adult": False,
        **kw,
    }


def series(
    tmdb_id, name, date_, *, episodes=20, votes=2000, rating=8.0, character="Lead", **kw
):
    # No "order" key: TMDB does not send billing order for TV cast credits.
    return {
        "media_type": "tv",
        "id": tmdb_id,
        "name": name,
        "original_name": name,
        "first_air_date": date_,
        "first_credit_air_date": date_,
        "episode_count": episodes,
        "vote_count": votes,
        "vote_average": rating,
        "popularity": kw.pop("popularity", 10.0),
        "character": character,
        "genre_ids": kw.pop("genre_ids", [18]),
        "poster_path": "/p.jpg",
        "adult": False,
        **kw,
    }


CAST = [
    movie(1, "Old Classic", "1990-05-01", rating=8.0, votes=3000),
    movie(2, "Recent Hit", "2022-03-01", rating=7.9, votes=9000),
    movie(3, "Cameo", "2015-01-01", order=40, rating=9.0, votes=20000),  # not lead
    movie(4, "Hyped Indie", "2019-01-01", rating=9.5, votes=40),  # too few votes
    movie(5, "Award Show", "2020-01-01", character="Self"),  # noise
    movie(6, "Undated Project", ""),
    movie(7, "Next Year Film", FUTURE),
    movie(550, "Shared Id Movie", "1999-10-15", rating=8.4, votes=27000),
    # Same movie twice (two characters): must merge into one entry.
    movie(
        2,
        "Recent Hit",
        "2022-03-01",
        rating=7.9,
        votes=9000,
        character="Narrator",
        order=3,
    ),
    series(550, "Shared Id Series", "2008-01-20", episodes=62, rating=8.9, votes=18000),
    series(20, "Guest Spot Show", "2001-01-01", episodes=1, rating=9.1, votes=5000),
    series(21, "Late Night Talk", "2010-01-01", episodes=30, genre_ids=[10767]),
    series(22, "Small Series", "2005-01-01", episodes=10, votes=100),  # under tv floor
]
CREW = [
    {
        "media_type": "tv",
        "id": 550,
        "name": "Shared Id Series",
        "first_air_date": "2008-01-20",
        "job": "Director",
        "department": "Directing",
        "vote_count": 18000,
        "vote_average": 8.9,
    },
    {
        "media_type": "tv",
        "id": 550,
        "name": "Shared Id Series",
        "first_air_date": "2008-01-20",
        "job": "Producer",
        "department": "Production",
        "vote_count": 18000,
        "vote_average": 8.9,
    },
]


def tmdb(cast=None, crew=None, people=None, details=None):
    client = MagicMock()
    client.get_person_combined_credits.return_value = {
        "cast": CAST if cast is None else cast,
        "crew": CREW if crew is None else crew,
    }
    # TMDB person search is case-insensitive.
    people = {k.casefold(): v for k, v in (people or {}).items()}
    client.search_person.side_effect = lambda q: {
        "results": list(people.get(q.casefold(), []))
    }
    details = details or {}

    def get_details(person_id, language="tr-TR"):
        if person_id == 404:
            raise TMDBNotFoundError("nope")
        return details.get(language[:2], {"id": person_id, "name": "Bryan Cranston"})

    client.get_person_details.side_effect = get_details
    return client


def person(pid, name, popularity, dept="Acting"):
    return {
        "id": pid,
        "name": name,
        "popularity": popularity,
        "known_for_department": dept,
        "profile_path": "/x.jpg",
        "known_for": [{"title": f"{name} film"}],
        "adult": False,
    }


@pytest.fixture
def client_with():
    patchers = []

    def use(fake):
        p1 = patch("apps.people.views.TMDBClient", return_value=fake)
        patchers.append(p1)
        p1.start()
        return fake

    yield use
    for p in patchers:
        p.stop()


# ---------------------------------------------------------------------------
# credits helpers
# ---------------------------------------------------------------------------


def test_merge_joins_characters_and_keeps_best_billing():
    merged = merge_credits(CAST)
    hit = next(m for m in merged if m["id"] == 2)
    assert hit["characters"] == ["Hero", "Narrator"]
    assert hit["order"] == 0
    assert len([m for m in merged if m["id"] == 2]) == 1


def test_merge_keeps_movie_and_series_with_same_id_apart():
    merged = merge_credits(CAST)
    assert {(m["media_type"], m["id"]) for m in merged if m["id"] == 550} == {
        ("movie", 550),
        ("tv", 550),
    }


@pytest.mark.parametrize(
    "item, noise",
    [
        (movie(1, "x", "2000", character="Self"), True),
        (movie(1, "x", "2000", character="Himself (archive footage)"), True),
        (movie(1, "x", "2000", character="Jim Gordon (voice)"), False),
        (movie(1, "x", "2000", character=""), False),
        (series(1, "x", "2000", genre_ids=[10764]), True),
        (series(1, "x", "2000", genre_ids=[18]), False),
        (movie(1, "x", "2000", adult=True), True),
    ],
)
def test_noise_detection(item, noise):
    assert is_noise(item) is noise


def test_lead_rules_differ_for_movies_and_series():
    assert is_lead(movie(1, "x", "2000", order=4))
    assert not is_lead(movie(1, "x", "2000", order=5))
    assert not is_lead({**movie(1, "x", "2000"), "order": None})
    assert is_lead(series(1, "x", "2000", episodes=3))
    assert not is_lead(series(1, "x", "2000", episodes=2))


def test_sorting_puts_undated_last_in_every_mode():
    items = merge_credits(
        [movie(1, "a", "2001-01-01"), movie(2, "b", ""), movie(3, "c", "1999-01-01")]
    )
    for mode in ("newest", "oldest", "rating", "popularity"):
        assert sort_credits(items, mode)[-1]["id"] == 2
    assert [i["id"] for i in sort_credits(items, "oldest")] == [3, 1, 2]
    assert [i["id"] for i in sort_credits(items, "newest")] == [1, 3, 2]


def test_rating_sort_puts_low_vote_titles_after_trusted_ones():
    items = [
        movie(1, "hyped", "2000", rating=9.8, votes=10),
        movie(2, "solid", "2000", rating=7.0),
    ]
    assert [i["id"] for i in sort_credits(items, "rating")] == [2, 1]


def test_split_upcoming_uses_today():
    released, upcoming = split_upcoming(
        [movie(1, "a", TODAY.isoformat()), movie(2, "b", FUTURE), movie(3, "c", "")],
        TODAY,
    )
    assert [i["id"] for i in released] == [1, 3]
    assert [i["id"] for i in upcoming] == [2]


def test_title_reason_is_localized_and_keeps_character_commas():
    item = {
        **series(1, "x", "2000", episodes=62, votes=18781, rating=8.9),
        "characters": ["Walter White, Heisenberg"],
    }
    assert (
        title_reason(item, "tr")
        == "Walter White, Heisenberg rolüyle, 62 bölüm · TMDB'de 18.781 oyla 8.9/10."
    )
    assert (
        title_reason(item, "en")
        == "As Walter White, Heisenberg, 62 episodes · TMDB 8.9/10 from 18,781 votes."
    )


# ---------------------------------------------------------------------------
# resolver
# ---------------------------------------------------------------------------

RDJ = person(3223, "Robert Downey Jr.", 11.3)


def test_alias_rdj_resolves_to_robert_downey_jr():
    fake = tmdb(
        people={"Robert Downey Jr.": [RDJ], "RDJ": [person(1, "rdj's character", 0.1)]}
    )
    result = PersonResolver(fake).resolve("RDJ")
    assert (result.status, result.person["name"]) == ("found", "Robert Downey Jr.")


def test_single_name_person():
    fake = tmdb(
        people={
            "Zendaya": [
                person(505710, "Zendaya", 20.0),
                person(2, "Zendaya Scott", 0.4),
            ]
        }
    )
    result = PersonResolver(fake).resolve("zendaya")
    assert result.person["tmdb_id"] == 505710


def test_typo_falls_back_to_fuzzy_surname_search():
    cranston = person(17419, "Bryan Cranston", 7.2)
    fake = tmdb(
        people={
            "Brayn Cranston": [],
            "Cranston": [cranston, person(9, "Fred Cranston", 0.2)],
        }
    )
    result = PersonResolver(fake).resolve("Brayn Cranston")
    assert (result.status, result.person["tmdb_id"]) == ("found", 17419)


def test_unknown_name_is_not_found():
    assert PersonResolver(tmdb()).resolve("Qwerty Asdf").status == "not_found"


def test_same_name_with_clear_favourite_is_found_with_alternatives():
    fake = tmdb(
        people={
            "Chris Evans": [
                person(16828, "Chris Evans", 8.2),
                person(1212362, "Chris Evans", 1.2, "Writing"),
            ]
        }
    )
    result = PersonResolver(fake).resolve("Chris Evans")
    assert result.status == "found"
    assert result.person["tmdb_id"] == 16828
    assert [c["tmdb_id"] for c in result.candidates] == [1212362]


def test_same_name_without_clear_favourite_is_ambiguous():
    fake = tmdb(
        people={
            "John Smith": [
                person(1, "John Smith", 2.0),
                person(2, "John Smith", 1.5, "Directing"),
            ]
        }
    )
    result = PersonResolver(fake).resolve("John Smith")
    assert result.status == "ambiguous"
    assert {c["tmdb_id"] for c in result.candidates} == {1, 2}
    assert result.person is None


def test_adult_people_are_ignored():
    fake = tmdb(people={"X Y": [{**person(1, "X Y", 5.0), "adult": True}]})
    assert PersonResolver(fake).resolve("X Y").status == "not_found"


# ---------------------------------------------------------------------------
# POST /api/v1/people/top-titles/
# ---------------------------------------------------------------------------

TOP_URL = "/api/v1/people/top-titles/"


def test_top_titles_two_sections_with_rules_applied(api_client, client_with):
    client_with(tmdb(people={"Bryan Cranston": [person(17419, "Bryan Cranston", 7.2)]}))
    body = api_client.post(TOP_URL, {"name": "Bryan Cranston"}, format="json").json()

    assert body["status"] == "found"
    movies = [m["tmdb_id"] for m in body["sections"]["movies"]]
    series_ids = [s["tmdb_id"] for s in body["sections"]["series"]]
    assert movies == [550, 1, 2]  # cameo, low-vote, Self, undated and future excluded
    assert series_ids == [550]  # guest spot, talk show and under-floor series excluded
    assert all(m["reason"] for m in body["sections"]["movies"])


def test_top_titles_movie_only_returns_only_movies(api_client, client_with):
    client_with(tmdb(people={"RDJ": [], "Robert Downey Jr.": [RDJ]}))
    body = api_client.post(
        TOP_URL, {"name": "RDJ", "media_type": "movie"}, format="json"
    ).json()
    assert list(body["sections"]) == ["movies"]
    assert body["person"]["name"] == "Robert Downey Jr."


def test_top_titles_series_only_excludes_guest_roles(api_client, client_with):
    client_with(tmdb(people={"Bryan Cranston": [person(17419, "Bryan Cranston", 7.2)]}))
    body = api_client.post(
        TOP_URL, {"name": "Bryan Cranston", "media_type": "tv"}, format="json"
    ).json()
    assert list(body["sections"]) == ["series"]
    assert all(s["episode_count"] >= 3 for s in body["sections"]["series"])


def test_top_titles_caps_each_section_at_ten(api_client, client_with):
    many = [movie(i, f"M{i}", "2000-01-01", rating=7 + i / 100) for i in range(1, 16)]
    client_with(tmdb(cast=many, crew=[], people={"A B": [person(1, "A B", 5.0)]}))
    body = api_client.post(
        TOP_URL, {"name": "A B", "media_type": "movie"}, format="json"
    ).json()
    ratings = [m["vote_average"] for m in body["sections"]["movies"]]
    assert len(ratings) == 10 and ratings == sorted(ratings, reverse=True)


def test_top_titles_by_person_id(api_client, client_with):
    client_with(tmdb())
    body = api_client.post(TOP_URL, {"person_id": 17419}, format="json").json()
    assert body["person"]["tmdb_id"] == 17419
    assert "movies" in body["sections"]


def test_top_titles_not_found_is_polite_404(api_client, client_with):
    client_with(tmdb())
    response = api_client.post(
        TOP_URL, {"name": "Qwerty Asdf", "lang": "en"}, format="json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()["error"]
    assert error["code"] == "person_not_found"
    assert "e.g." in error["message"] and error["details"] == {"query": "Qwerty Asdf"}


def test_top_titles_ambiguous_returns_candidates_without_titles(
    api_client, client_with
):
    fake = client_with(
        tmdb(
            people={
                "John Smith": [
                    person(1, "John Smith", 2.0),
                    person(2, "John Smith", 1.5),
                ]
            }
        )
    )
    body = api_client.post(TOP_URL, {"name": "John Smith"}, format="json").json()
    assert body["status"] == "ambiguous" and len(body["candidates"]) == 2
    assert "sections" not in body
    fake.get_person_combined_credits.assert_not_called()


def test_top_titles_requires_name_or_id(api_client, client_with):
    client_with(tmdb())
    response = api_client.post(TOP_URL, {"media_type": "tv"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_top_titles_tmdb_down_is_503(api_client, client_with):
    fake = tmdb()
    fake.search_person.side_effect = TMDBServiceUnavailableError("down")
    client_with(fake)
    response = api_client.post(TOP_URL, {"name": "X"}, format="json")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_missing_tmdb_key_is_503_not_500(api_client, settings):
    settings.TMDB_API_KEY = ""
    response = api_client.post(TOP_URL, {"name": "X"}, format="json")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ---------------------------------------------------------------------------
# GET /api/v1/people/{id}/filmography/
# ---------------------------------------------------------------------------


def filmography(api_client, **params):
    response = api_client.get("/api/v1/people/17419/filmography/", params)
    assert response.status_code == status.HTTP_200_OK, response.content
    return response.json()


def test_filmography_oldest_is_chronological(api_client, client_with):
    client_with(tmdb())
    body = filmography(api_client, sort="oldest", lead_only="false")
    dates = [r["release_date"] for r in body["results"]]
    dated = [d for d in dates if d]
    assert dated == sorted(dated)
    assert dates[-1] == ""  # undated last


def test_filmography_newest_starts_from_most_recent(api_client, client_with):
    client_with(tmdb())
    body = filmography(api_client, sort="newest", lead_only="false")
    dated = [r["release_date"] for r in body["results"] if r["release_date"]]
    assert dated == sorted(dated, reverse=True)
    assert body["results"][0]["title"] == "Recent Hit"
    assert body["results"][-1]["title"] == "Undated Project"


def test_filmography_future_titles_go_to_upcoming(api_client, client_with):
    client_with(tmdb())
    body = filmography(api_client)
    assert [u["title"] for u in body["upcoming"]] == ["Next Year Film"]
    assert "Next Year Film" not in [r["title"] for r in body["results"]]


def test_filmography_hides_noise_by_default_and_shows_it_on_request(
    api_client, client_with
):
    client_with(tmdb())
    default = filmography(api_client, lead_only="false")
    titles = {r["title"] for r in default["results"]}
    assert "Award Show" not in titles and "Late Night Talk" not in titles
    assert default["hidden_noise_count"] == 2

    everything = filmography(api_client, lead_only="false", include_all="true")
    assert {"Award Show", "Late Night Talk"} <= {
        r["title"] for r in everything["results"]
    }


def test_filmography_lead_only_default_drops_cameos_and_guest_spots(
    api_client, client_with
):
    client_with(tmdb())
    titles = {r["title"] for r in filmography(api_client)["results"]}
    assert "Cameo" not in titles and "Guest Spot Show" not in titles
    assert {"Recent Hit", "Shared Id Series"} <= titles


def test_filmography_media_type_filter_and_same_id(api_client, client_with):
    client_with(tmdb())
    both = filmography(api_client, lead_only="false")
    assert {("movie", 550), ("tv", 550)} <= {
        (r["media_type"], r["tmdb_id"]) for r in both["results"]
    }
    tv = filmography(api_client, media_type="tv", lead_only="false")
    assert {r["media_type"] for r in tv["results"]} == {"tv"}


def test_filmography_series_entries_show_episodes_and_first_year(
    api_client, client_with
):
    client_with(tmdb())
    show = next(
        r
        for r in filmography(api_client)["results"]
        if r["tmdb_id"] == 550 and r["media_type"] == "tv"
    )
    assert (show["episode_count"], show["first_credit_year"]) == (62, 2008)


def test_filmography_crew_roles(api_client, client_with):
    client_with(tmdb())
    body = filmography(api_client, role="directing")
    assert [(r["title"], r["jobs"]) for r in body["results"]] == [
        ("Shared Id Series", ["Director"])
    ]


def test_filmography_pagination(api_client, client_with):
    many = [movie(i, f"M{i}", f"{1980 + i}-01-01") for i in range(1, 46)]
    client_with(tmdb(cast=many, crew=[]))
    page1 = filmography(api_client)
    page3 = filmography(api_client, page=3)
    assert (page1["total_results"], page1["total_pages"]) == (45, 3)
    assert len(page1["results"]) == 20 and len(page3["results"]) == 5
    assert page3["upcoming"] == []


@pytest.mark.parametrize(
    "params", [{"sort": "random"}, {"role": "acting-ish"}, {"page": "x"}]
)
def test_filmography_rejects_bad_params(api_client, client_with, params):
    client_with(tmdb())
    response = api_client.get("/api/v1/people/17419/filmography/", params)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_filmography_unknown_person_is_404(api_client, client_with):
    client_with(tmdb())
    assert api_client.get("/api/v1/people/404/filmography/").status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/people/{id}/  and search
# ---------------------------------------------------------------------------


def test_detail_falls_back_to_english_biography(api_client, client_with):
    client_with(
        tmdb(
            details={
                "tr": {
                    "id": 17419,
                    "name": "Bryan Cranston",
                    "biography": "",
                    "birthday": "1956-03-07",
                },
                "en": {
                    "id": 17419,
                    "name": "Bryan Cranston",
                    "biography": "Bryan Lee Cranston is...",
                },
            }
        )
    )
    body = api_client.get("/api/v1/people/17419/").json()
    assert body["biography"].startswith("Bryan Lee Cranston")
    assert (body["biography_language"], body["biography_is_fallback"]) == ("en", True)
    assert body["birth_year"] == 1956
    assert [k["title"] for k in body["known_for"]][:2] == [
        "Shared Id Movie",
        "Shared Id Series",
    ]


def test_detail_keeps_turkish_biography_when_present(api_client, client_with):
    client_with(
        tmdb(details={"tr": {"id": 1, "name": "A", "biography": "Türkçe biyografi"}})
    )
    body = api_client.get("/api/v1/people/1/").json()
    assert (body["biography"], body["biography_is_fallback"]) == (
        "Türkçe biyografi",
        False,
    )


def test_detail_not_found(api_client, client_with):
    client_with(tmdb())
    response = api_client.get("/api/v1/people/404/?lang=en")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "No person exists with this id."


def test_person_search(api_client, client_with):
    client_with(tmdb(people={"cranston": [person(17419, "Bryan Cranston", 7.2)]}))
    body = api_client.get("/api/v1/people/search/", {"query": "cranston"}).json()
    assert body["count"] == 1 and body["results"][0]["tmdb_id"] == 17419
    assert api_client.get("/api/v1/people/search/").status_code == 400
