"""Faz 7C tests: profiles, lists, notebook sharing, community, moderation, blocks."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from apps.accounts.models import Notification
from apps.accounts.services import delete_account, export_user_data
from apps.catalog.tmdb_client import TMDBNotFoundError
from apps.notebook.models import NotebookEntry
from apps.social.models import NotebookShare, Profile, Report, UserList, UserListItem
from apps.social.services import SocialError, create_list, report, update_profile
from apps.social.text import clean_text, contains_banned_word, username_problem
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
User = get_user_model()


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
            "release_date": "2010-07-16",
            "poster_path": "/p.jpg",
        }

    def tv(tmdb_id, language="tr-TR"):
        return {
            "name": f"Dizi {tmdb_id}",
            "first_air_date": "2008-01-20",
            "poster_path": "/s.jpg",
        }

    client.get_movie_detail.side_effect = movie
    client.get_tv_detail.side_effect = tv
    return client


@pytest.fixture(autouse=True)
def tmdb():
    client = fake_tmdb()
    with patch("apps.social.views.TMDBClient", return_value=client):
        yield client


def make_user(name: str, visibility: str | None = "public", age_days: int = 10):
    user = User.objects.create_user(email=f"{name}@example.com", password="x")
    User.objects.filter(pk=user.pk).update(
        date_joined=timezone.now() - timedelta(days=age_days)
    )
    user.refresh_from_db()
    if visibility:
        Profile.objects.create(user=user, username=name, profile_visibility=visibility)
    return user


def client_for(user=None) -> APIClient:
    client = APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


def make_list(owner, visibility="public", n_items=0, **extra) -> UserList:
    user_list = UserList.objects.create(
        owner=owner,
        slug=f"s{UserList.objects.count()}x{owner.pk}",
        title="Liste",
        visibility=visibility,
        **extra,
    )
    for i in range(n_items):
        UserListItem.objects.create(
            user_list=user_list, media_type="movie", tmdb_id=i + 1, position=i + 1
        )
    return user_list


@pytest.fixture
def ada():
    return make_user("ada")


@pytest.fixture
def bob():
    return make_user("bob")


# --- Visibility matrix ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "visibility,guest_status",
    [("public", 200), ("unlisted", 200), ("private", 404)],
)
def test_profile_visibility_for_guest(visibility, guest_status):
    make_user("cem", visibility)
    response = client_for().get("/api/v1/users/cem/")
    assert response.status_code == guest_status
    if guest_status == 200:
        assert response["X-Robots-Tag"].startswith("noindex")
        assert "no-store" in response["Cache-Control"]


def test_private_profile_visible_to_owner_and_case_insensitive_url():
    cem = make_user("cem", "private")
    assert client_for(cem).get("/api/v1/users/CEM/").json()["is_owner"] is True


def test_not_visible_and_missing_look_identical(ada):
    make_user("cem", "private")
    hidden = client_for(ada).get("/api/v1/users/cem/")
    missing = client_for(ada).get("/api/v1/users/nobody_here/")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json() == missing.json()


@pytest.mark.parametrize(
    "visibility,status_code",
    [("public", 200), ("unlisted", 200), ("private", 404)],
)
def test_list_by_link(ada, visibility, status_code):
    user_list = make_list(ada, visibility, n_items=2)
    assert (
        client_for().get(f"/api/v1/lists/{user_list.slug}/").status_code == status_code
    )


def test_profile_lists_only_public_ones(ada):
    public = make_list(ada, "public")
    make_list(ada, "unlisted")
    make_list(ada, "private")
    slugs = [
        lst["slug"] for lst in client_for().get("/api/v1/users/ada/").json()["lists"]
    ]
    assert slugs == [public.slug]
    own = client_for(ada).get("/api/v1/users/ada/").json()["lists"]
    assert len(own) == 3


def test_public_entries_shown_only_when_profile_is_public():
    for visibility in ("public", "unlisted"):
        user = make_user(f"u_{visibility}", visibility)
        NotebookEntry.objects.create(
            user=user,
            media_type="movie",
            tmdb_id=1,
            rating_x2=8,
            visibility="public",
            is_favorite=True,
        )
        NotebookEntry.objects.create(
            user=user, media_type="movie", tmdb_id=2, rating_x2=6
        )  # private
        data = client_for().get(f"/api/v1/users/u_{visibility}/").json()
        expected = 1 if visibility == "public" else 0
        assert len(data["recent_ratings"]) == expected
        assert len(data["favorites"]) == expected


def test_list_owner_hidden_when_profile_private():
    cem = make_user("cem", "private")
    user_list = make_list(cem, "unlisted")
    assert client_for().get(f"/api/v1/lists/{user_list.slug}/").json()["owner"] is None


def test_stats_only_when_enabled(ada):
    assert "stats" not in client_for().get("/api/v1/users/ada/").json()
    Profile.objects.filter(user=ada).update(show_stats=True)
    assert "stats" in client_for().get("/api/v1/users/ada/").json()


# --- Guests vs writes --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/api/v1/me/profile/"),
        ("post", "/api/v1/me/lists/"),
        ("post", "/api/v1/me/shares/"),
        ("post", "/api/v1/reports/"),
        ("post", "/api/v1/me/blocks/"),
    ],
)
def test_guest_cannot_write(method, url):
    assert getattr(client_for(), method)(url, {}, format="json").status_code in (
        401,
        403,
    )


def test_guest_cannot_clone(ada):
    user_list = make_list(ada)
    assert client_for().post(f"/api/v1/lists/{user_list.slug}/clone/").status_code in (
        401,
        403,
    )


# --- Profile & username ---------------------------------------------------------------------------


def test_profile_create_and_username_rules():
    dan = make_user("dan_tmp", visibility=None)
    client = client_for(dan)
    assert client.get("/api/v1/me/profile/").json()["username"] == ""
    assert (
        client.patch("/api/v1/me/profile/", {"bio": "hi"}, format="json").status_code
        == 400
    )
    ok = client.patch("/api/v1/me/profile/", {"username": "Dan_Fan"}, format="json")
    assert ok.status_code == 200
    assert ok.json()["username"] == "dan_fan"
    assert ok.json()["profile_visibility"] == "private"  # private by default


@pytest.mark.parametrize(
    "username,code",
    [
        ("ab", "invalid_username"),
        ("ada-lovelace", "invalid_username"),
        ("çiçek", "invalid_username"),
        ("admin", "reserved_username"),
        ("bitch_lord", "banned_word"),
        ("ada", "username_taken"),
    ],
)
def test_bad_usernames(ada, username, code):
    dan = make_user("dan", visibility=None)
    response = client_for(dan).patch(
        "/api/v1/me/profile/", {"username": username}, format="json"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == code


def test_username_change_interval(ada):
    update_profile(ada, {"username": "ada_2"})
    with pytest.raises(SocialError, match="username_change_too_soon"):
        update_profile(ada, {"username": "ada_3"})
    Profile.objects.filter(user=ada).update(
        username_changed_at=timezone.now() - timedelta(days=31)
    )
    assert update_profile(ada, {"username": "ada_3"}).username == "ada_3"


def test_text_is_sanitised(ada):
    response = client_for(ada).patch(
        "/api/v1/me/profile/",
        {"bio": "<script>alert(1)</script> bak https://spam.example.com ve www.x.io"},
        format="json",
    )
    bio = response.json()["bio"]
    assert "<script>" in bio  # kept as plain text; the web app renders text, never HTML
    assert "http" not in bio and "www" not in bio
    banned = client_for(ada).patch(
        "/api/v1/me/profile/", {"bio": "SHIT film"}, format="json"
    )
    assert banned.json()["error"]["code"] == "banned_word"


def test_text_helpers():
    assert clean_text("a   b\n c site.com") == "a b c"
    assert contains_banned_word("Siktir git")
    assert not contains_banned_word("got a picture of Sikkim")
    assert username_problem("good_name") is None


# --- Lists ------------------------------------------------------------------------------------------


def test_list_crud_and_items(ada, tmdb):
    client = client_for(ada)
    created = client.post("/api/v1/me/lists/", {"title": "En iyiler"}, format="json")
    assert created.status_code == 201
    pk = created.json()["id"]
    items = [
        {"media_type": "movie", "tmdb_id": 1},
        {"media_type": "tv", "tmdb_id": 1},  # same id, other media type: separate item
        {"media_type": "movie", "tmdb_id": 2, "comment": "favori"},
    ]
    response = client.put(
        f"/api/v1/me/lists/{pk}/items/", {"items": items}, format="json"
    )
    assert response.status_code == 200
    titles = [i["title"] for i in response.json()["items"]]
    assert titles == ["Film 1", "Dizi 1", "Film 2"]
    assert tmdb.get_movie_detail.call_count == 2

    # Reorder: no new TMDB calls, positions follow the order sent.
    reordered = client.put(
        f"/api/v1/me/lists/{pk}/items/", {"items": items[::-1]}, format="json"
    )
    assert [i["title"] for i in reordered.json()["items"]] == [
        "Film 2",
        "Dizi 1",
        "Film 1",
    ]
    assert [i["position"] for i in reordered.json()["items"]] == [1, 2, 3]
    assert tmdb.get_movie_detail.call_count == 2

    patched = client.patch(
        f"/api/v1/me/lists/{pk}/", {"visibility": "unlisted"}, format="json"
    )
    assert patched.json()["visibility"] == "unlisted"
    assert client.delete(f"/api/v1/me/lists/{pk}/").status_code == 204
    assert not UserListItem.objects.exists()


def test_duplicate_items_rejected_and_list_unchanged(ada):
    user_list = make_list(ada, n_items=2)
    dup = [{"media_type": "movie", "tmdb_id": 9}, {"media_type": "movie", "tmdb_id": 9}]
    response = client_for(ada).put(
        f"/api/v1/me/lists/{user_list.pk}/items/", {"items": dup}, format="json"
    )
    assert response.json()["error"]["code"] == "duplicate_item"
    assert user_list.items.count() == 2


def test_unknown_title_rejected_atomically(ada):
    user_list = make_list(ada, n_items=2)
    items = [
        {"media_type": "movie", "tmdb_id": 5},
        {"media_type": "movie", "tmdb_id": 404},
    ]
    response = client_for(ada).put(
        f"/api/v1/me/lists/{user_list.pk}/items/", {"items": items}, format="json"
    )
    assert response.status_code == 404
    assert list(user_list.items.values_list("tmdb_id", flat=True)) == [1, 2]


def test_list_limits(ada):
    for _ in range(UserList.MAX_PER_USER):
        make_list(ada)
    response = client_for(ada).post("/api/v1/me/lists/", {"title": "51"}, format="json")
    assert response.json()["error"]["code"] == "too_many_lists"

    user_list = UserList.objects.filter(owner=ada).first()
    items = [
        {"media_type": "movie", "tmdb_id": i} for i in range(1, UserList.MAX_ITEMS + 2)
    ]
    too_many = client_for(ada).put(
        f"/api/v1/me/lists/{user_list.pk}/items/", {"items": items}, format="json"
    )
    assert too_many.status_code == 400


def test_daily_list_creation_limit(ada):
    with patch("apps.social.services.DAILY_LIST_CREATIONS", 2):
        create_list(ada, {"title": "a"})
        create_list(ada, {"title": "b"})
        with pytest.raises(SocialError, match="daily_limit"):
            create_list(ada, {"title": "c"})


def test_idor_on_someone_elses_list(ada, bob):
    user_list = make_list(ada, "public", n_items=1)
    client = client_for(bob)
    assert client.get(f"/api/v1/me/lists/{user_list.pk}/").status_code == 404
    assert (
        client.patch(
            f"/api/v1/me/lists/{user_list.pk}/", {"title": "x"}, format="json"
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/me/lists/{user_list.pk}/").status_code == 404
    put = client.put(
        f"/api/v1/me/lists/{user_list.pk}/items/", {"items": []}, format="json"
    )
    assert put.status_code == 404
    assert user_list.items.count() == 1


def test_clone_and_random(ada, bob):
    user_list = make_list(ada, "unlisted", n_items=3)
    copy = client_for(bob).post(f"/api/v1/lists/{user_list.slug}/clone/")
    assert copy.status_code == 201
    assert copy.json()["item_count"] == 3
    assert copy.json()["visibility"] == "private"

    private = make_list(ada, "private", n_items=1)
    assert (
        client_for(bob).post(f"/api/v1/lists/{private.slug}/clone/").status_code == 404
    )

    pick = (
        client_for()
        .get(f"/api/v1/lists/{user_list.slug}/random/?exclude=movie:1,movie:2")
        .json()["pick"]
    )
    assert pick["tmdb_id"] == 3


# --- Notebook sharing ---------------------------------------------------------------------------------


@pytest.fixture
def notebook(ada):
    NotebookEntry.objects.create(
        user=ada,
        media_type="movie",
        tmdb_id=1,
        status="watched",
        rating_x2=9,
        note="open",
    )
    NotebookEntry.objects.create(
        user=ada,
        media_type="movie",
        tmdb_id=2,
        status="watched",
        note="secret",
        note_locked=True,
    )
    NotebookEntry.objects.create(
        user=ada, media_type="tv", tmdb_id=3, status="want_to_watch", note="later"
    )
    return ada


def share(user, **body):
    return client_for(user).post("/api/v1/me/shares/", body, format="json").json()


def test_share_ratings_scope_has_no_notes(notebook):
    created = share(notebook)
    assert "token" in created and "warning" not in created
    stored = NotebookShare.objects.get()
    assert created["token"] not in stored.token_hash  # only the hash is kept
    body = client_for().get(f"/api/v1/shared/{created['token']}/").json()
    assert len(body["entries"]) == 3
    assert all("note" not in e for e in body["entries"])
    stored.refresh_from_db()
    assert stored.view_count == 1


def test_share_with_notes_respects_lock_and_statuses(notebook):
    created = share(notebook, scope="ratings_notes", statuses=["watched"])
    assert created["warning"]
    entries = client_for().get(f"/api/v1/shared/{created['token']}/").json()["entries"]
    notes = {e["tmdb_id"]: e.get("note") for e in entries}
    assert notes == {1: "open", 2: None}


def test_revoked_or_expired_share_is_404(notebook):
    created = share(notebook)
    url = f"/api/v1/shared/{created['token']}/"
    assert (
        client_for(notebook).delete(f"/api/v1/me/shares/{created['id']}/").status_code
        == 204
    )
    assert client_for().get(url).status_code == 404

    expiring = share(notebook, expires_in_days=1)
    NotebookShare.objects.filter(pk=expiring["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert client_for().get(f"/api/v1/shared/{expiring['token']}/").status_code == 404
    assert client_for().get("/api/v1/shared/not-a-token/").status_code == 404


def test_cannot_revoke_someone_elses_share(notebook, bob):
    created = share(notebook)
    assert (
        client_for(bob).delete(f"/api/v1/me/shares/{created['id']}/").status_code == 404
    )
    assert client_for().get(f"/api/v1/shared/{created['token']}/").status_code == 200


# --- Community ----------------------------------------------------------------------------------------------


def test_community_threshold_and_raters():
    users = [make_user(f"rater{i}", "public" if i < 2 else "private") for i in range(5)]
    for user in users[:4]:
        NotebookEntry.objects.create(
            user=user, media_type="movie", tmdb_id=7, rating_x2=8, visibility="public"
        )
    url = "/api/v1/titles/movie/7/community/"
    four = client_for().get(url).json()
    assert four["average"] is None and four["votes"] is None
    assert {r["username"] for r in four["raters"]} == {
        "rater0",
        "rater1",
    }  # private profiles never listed

    NotebookEntry.objects.create(
        user=users[4], media_type="movie", tmdb_id=7, rating_x2=10
    )
    five = client_for().get(url).json()
    assert five["votes"] == 5
    assert five["average"] == 4.2
    assert client_for().get("/api/v1/titles/person/7/community/").status_code == 404


# --- Moderation & blocks --------------------------------------------------------------------------------------


def test_reports_auto_hide_after_three_counting_reporters(ada):
    user_list = make_list(ada, "public")
    newbie = make_user("newbie", age_days=0)
    reporters = [make_user(f"rep{i}") for i in range(3)]

    def send(user):
        body = {"target_type": "list", "target_id": user_list.pk, "reason": "spam"}
        return client_for(user).post("/api/v1/reports/", body, format="json")

    assert send(newbie).status_code == 201  # recorded but does not count (< 24 h)
    send(reporters[0])
    send(reporters[0])  # repeat is not counted twice
    send(reporters[1])
    user_list.refresh_from_db()
    assert not user_list.is_hidden
    send(reporters[2])
    user_list.refresh_from_db()
    assert user_list.is_hidden
    assert client_for().get(f"/api/v1/lists/{user_list.slug}/").status_code == 404
    assert (
        client_for(ada).get(f"/api/v1/lists/{user_list.slug}/").status_code == 200
    )  # owner still sees it
    assert (
        Notification.objects.filter(
            user=ada, kind=Notification.Kind.CONTENT_HIDDEN
        ).count()
        == 1
    )
    assert Report.objects.count() == 4


def test_cannot_report_own_content(ada):
    with pytest.raises(SocialError, match="invalid_target"):
        report(ada, "profile", ada.profile.pk, "spam", "")


def test_admin_unhide_action(ada, admin_client):
    profile = ada.profile
    profile.is_hidden = True
    profile.save()
    item = Report.objects.create(
        reporter=make_user("rep"),
        target_type="profile",
        target_id=profile.pk,
        reason="abuse",
    )
    response = admin_client.post(
        "/admin/social/report/",
        {"action": "unhide_target", "_selected_action": [item.pk]},
    )
    assert response.status_code == 302
    profile.refresh_from_db()
    item.refresh_from_db()
    assert not profile.is_hidden and item.resolved_at is not None


def test_block_hides_both_ways(ada, bob):
    user_list = make_list(ada, "public")
    assert (
        client_for(bob)
        .post("/api/v1/me/blocks/", {"username": "ada"}, format="json")
        .status_code
        == 201
    )
    assert client_for(bob).get("/api/v1/me/blocks/").json() == ["ada"]
    assert client_for(bob).get("/api/v1/users/ada/").status_code == 404
    assert client_for(ada).get("/api/v1/users/bob/").status_code == 404
    assert client_for(ada).get(f"/api/v1/lists/{user_list.slug}/").status_code == 200
    assert client_for(bob).get(f"/api/v1/lists/{user_list.slug}/").status_code == 404
    assert client_for(bob).delete("/api/v1/me/blocks/ada/").status_code == 204
    assert client_for(bob).get("/api/v1/users/ada/").status_code == 200


def test_suspended_owner_disappears(ada):
    user_list = make_list(ada, "public")
    User.objects.filter(pk=ada.pk).update(is_active=False)
    assert client_for().get("/api/v1/users/ada/").status_code == 404
    assert client_for().get(f"/api/v1/lists/{user_list.slug}/").status_code == 404


# --- Account export & deletion ------------------------------------------------------------------------


def test_export_and_cascade(notebook, bob):
    make_list(notebook, n_items=1)
    share(notebook)
    data = export_user_data(notebook)
    assert data["social"]["profile"]["username"] == "ada"
    assert len(data["social"]["lists"]) == 1 and len(data["social"]["shares"]) == 1
    delete_account(notebook)
    assert not Profile.objects.filter(username="ada").exists()
    assert not UserList.objects.exists() and not NotebookShare.objects.exists()
