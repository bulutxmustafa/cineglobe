"""Faz 7 tests: optional accounts (session + CSRF), privacy, export and deletion."""

import json
import re
from unittest.mock import patch

import pytest
from apps.accounts.models import Notification, SearchHistory
from apps.accounts.views import unsubscribe_token
from apps.reminders.models import Reminder
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
User = get_user_model()
PASSWORD = "Sinema-2026!x"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()  # throttle counters
    yield
    cache.clear()


def register(client, email="ada@example.com", **extra):
    body = {"email": email, "password": PASSWORD, "age_confirmed": True, **extra}
    return client.post("/api/v1/auth/register/", body, format="json")


@pytest.fixture
def user():
    return User.objects.create_user(email="ada@example.com", password=PASSWORD)


@pytest.fixture
def signed_in(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


# ---------------------------------------------------------------------------
# Registration & sign-in
# ---------------------------------------------------------------------------


def test_register_creates_account_signs_in_and_hashes_password(api_client):
    response = register(api_client, email="  Ada@Example.COM ", preferred_language="en")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == "ada@example.com"
    user = User.objects.get()
    assert user.password != PASSWORD and not user.password.startswith(PASSWORD)
    assert user.check_password(PASSWORD)
    assert user.age_confirmed_at is not None and user.preferred_language == "en"
    assert api_client.get("/api/v1/me/").status_code == 200  # session cookie set


def test_register_requires_age_confirmation_and_strong_unique_email(api_client):
    no_age = register(api_client, age_confirmed=False)
    assert (
        no_age.status_code == 400
        and "age_confirmed" in no_age.json()["error"]["details"]
    )
    weak = api_client.post(
        "/api/v1/auth/register/",
        {"email": "b@example.com", "password": "123", "age_confirmed": True},
        format="json",
    )
    assert weak.status_code == 400
    register(api_client)
    duplicate = register(APIClient(), email="ADA@example.com")
    assert (
        duplicate.status_code == 400 and "email" in duplicate.json()["error"]["details"]
    )


def test_login_and_logout(api_client, user):
    bad = api_client.post(
        "/api/v1/auth/login/",
        {"email": "ada@example.com", "password": "nope"},
        format="json",
    )
    unknown = api_client.post(
        "/api/v1/auth/login/",
        {"email": "x@example.com", "password": "nope"},
        format="json",
    )
    assert bad.json()["error"] == unknown.json()["error"]  # no account probing
    ok = api_client.post(
        "/api/v1/auth/login/",
        {"email": "ADA@example.com", "password": PASSWORD},
        format="json",
    )
    assert ok.status_code == 200
    assert api_client.get("/api/v1/me/").status_code == 200
    assert api_client.post("/api/v1/auth/logout/").status_code == 204
    assert api_client.get("/api/v1/me/").status_code == status.HTTP_403_FORBIDDEN


def test_csrf_is_enforced_on_sign_in_and_on_signed_in_writes(user):
    client = APIClient(enforce_csrf_checks=True)
    creds = {"email": "ada@example.com", "password": PASSWORD}
    assert client.post("/api/v1/auth/login/", creds, format="json").status_code == 403
    token = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
    assert (
        client.post(
            "/api/v1/auth/login/", creds, format="json", HTTP_X_CSRFTOKEN=token
        ).status_code
        == 200
    )
    # A signed-in write without the token is refused too.
    assert (
        client.patch(
            "/api/v1/me/", {"preferred_language": "en"}, format="json"
        ).status_code
        == 403
    )
    token = client.cookies["csrftoken"].value
    assert (
        client.patch(
            "/api/v1/me/",
            {"preferred_language": "en"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        ).status_code
        == 200
    )


def test_sign_in_endpoints_are_throttled(api_client, user):
    from rest_framework.throttling import ScopedRateThrottle

    # DRF reads rates once at import, so patch the dict the throttle actually uses.
    rates = {**ScopedRateThrottle.THROTTLE_RATES, "auth": "3/min"}
    with patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
        codes = [
            api_client.post(
                "/api/v1/auth/login/",
                {"email": "ada@example.com", "password": "x"},
                format="json",
            ).status_code
            for _ in range(4)
        ]
    assert codes == [400, 400, 400, status.HTTP_429_TOO_MANY_REQUESTS]


def test_session_cookie_is_httponly_and_lax(api_client):
    response = register(api_client)
    cookie = response.cookies["sessionid"]
    assert cookie["httponly"] and cookie["samesite"] == "Lax"


# ---------------------------------------------------------------------------
# Guests keep everything (accounts are optional)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    ["/api/v1/collections/", "/api/v1/health/"],
)
def test_guest_endpoints_need_no_account(api_client, url):
    assert api_client.get(url).status_code == 200


@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/api/v1/me/"),
        ("get", "/api/v1/me/export/"),
        ("get", "/api/v1/me/search-history/"),
        ("get", "/api/v1/me/notifications/"),
        ("get", "/api/v1/reminders/"),
        ("post", "/api/v1/reminders/"),
        ("delete", "/api/v1/reminders/1/"),
    ],
)
def test_personal_endpoints_require_sign_in(api_client, method, url):
    assert getattr(api_client, method)(url).status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Profile, password, export, deletion
# ---------------------------------------------------------------------------


def test_update_preferences_but_not_email(signed_in, user):
    response = signed_in.patch(
        "/api/v1/me/",
        {
            "preferred_language": "en",
            "email_notifications": False,
            "email": "evil@example.com",
        },
        format="json",
    )
    user.refresh_from_db()
    assert response.status_code == 200
    assert (user.preferred_language, user.email_notifications, user.email) == (
        "en",
        False,
        "ada@example.com",
    )


def test_password_change_keeps_this_session(api_client, user):
    api_client.post(
        "/api/v1/auth/login/",
        {"email": "ada@example.com", "password": PASSWORD},
        format="json",
    )
    wrong = api_client.post(
        "/api/v1/auth/password/change/",
        {"current_password": "x", "new_password": "Yeni-Sifre-2026!"},
        format="json",
    )
    assert wrong.status_code == 400
    ok = api_client.post(
        "/api/v1/auth/password/change/",
        {"current_password": PASSWORD, "new_password": "Yeni-Sifre-2026!"},
        format="json",
    )
    assert ok.status_code == 204 and api_client.get("/api/v1/me/").status_code == 200
    user.refresh_from_db()
    assert user.check_password("Yeni-Sifre-2026!")


def test_password_reset_flow_and_no_account_enumeration(api_client, user):
    unknown = api_client.post(
        "/api/v1/auth/password/reset/", {"email": "nobody@example.com"}, format="json"
    )
    known = api_client.post(
        "/api/v1/auth/password/reset/", {"email": "ada@example.com"}, format="json"
    )
    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()
    assert len(mail.outbox) == 1
    uid, token = re.search(r"uid=([^&]+)&token=(\S+)", mail.outbox[0].body).groups()

    bad = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {"uid": uid, "token": "x", "new_password": "Yeni-Sifre-2026!"},
        format="json",
    )
    assert bad.status_code == 400
    ok = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {"uid": uid, "token": token, "new_password": "Yeni-Sifre-2026!"},
        format="json",
    )
    assert ok.status_code == 204
    reused = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {"uid": uid, "token": token, "new_password": "Baska-Sifre-2026!"},
        format="json",
    )
    assert reused.status_code == 400  # token dies once the password changes


def test_export_contains_my_data_only(signed_in, user):
    other = User.objects.create_user(email="other@example.com", password=PASSWORD)
    SearchHistory.objects.create(user=user, query="gerilim")
    SearchHistory.objects.create(user=other, query="gizli arama")
    Reminder.objects.create(user=user, media_type="movie", tmdb_id=1, title="Film")
    response = signed_in.get("/api/v1/me/export/")
    assert response["Content-Disposition"].startswith("attachment")
    data = json.loads(response.content)
    assert data["account"]["email"] == "ada@example.com"
    assert [s["query"] for s in data["search_history"]] == ["gerilim"]
    assert data["reminders"][0]["title"] == "Film"
    assert "gizli arama" not in response.content.decode()


def test_delete_account_removes_everything(api_client, user):
    api_client.post(
        "/api/v1/auth/login/",
        {"email": "ada@example.com", "password": PASSWORD},
        format="json",
    )
    SearchHistory.objects.create(user=user, query="x")
    Reminder.objects.create(user=user, media_type="movie", tmdb_id=1)
    Notification.objects.create(user=user, kind="reminder_due", message="m")
    assert (
        api_client.delete(
            "/api/v1/me/", {"password": "wrong"}, format="json"
        ).status_code
        == 400
    )
    assert (
        api_client.delete(
            "/api/v1/me/", {"password": PASSWORD}, format="json"
        ).status_code
        == 204
    )
    assert not User.objects.exists()
    assert (
        not SearchHistory.objects.exists()
        and not Reminder.objects.exists()
        and not Notification.objects.exists()
    )
    assert api_client.get("/api/v1/me/").status_code == 403


# ---------------------------------------------------------------------------
# Search history (recorded for signed-in users only; private)
# ---------------------------------------------------------------------------


@pytest.fixture
def search_stub():
    payload = {"ai_status": "fallback", "results": []}
    with patch("apps.search.views.SearchService") as service:
        service.return_value.search.side_effect = lambda *a, **k: dict(payload)
        yield


def test_search_history_recorded_only_when_signed_in(
    api_client, signed_in, user, search_stub
):
    api_client.post("/api/v1/search/", {"query": "misafir araması"}, format="json")
    signed_in.post("/api/v1/search/", {"query": "gerilim olsun"}, format="json")
    assert list(SearchHistory.objects.values_list("user_id", "query")) == [
        (user.pk, "gerilim olsun")
    ]


def test_search_response_reports_quota(api_client, search_stub, settings):
    settings.GUEST_DAILY_AI_SEARCHES = 10
    quota = api_client.post(
        "/api/v1/search/", {"query": "komedi"}, format="json"
    ).json()["quota"]
    assert quota == {
        "signed_in": False,
        "limit": 10,
        "remaining": 10,
        "suggest_signup": False,
    }


def test_search_history_is_private(signed_in, user):
    other = User.objects.create_user(email="other@example.com", password=PASSWORD)
    mine = SearchHistory.objects.create(user=user, query="benim")
    theirs = SearchHistory.objects.create(user=other, query="onun")
    assert [s["query"] for s in signed_in.get("/api/v1/me/search-history/").json()] == [
        "benim"
    ]
    assert (
        signed_in.delete(f"/api/v1/me/search-history/{theirs.pk}/").status_code == 404
    )
    assert signed_in.delete(f"/api/v1/me/search-history/{mine.pk}/").status_code == 204
    assert signed_in.delete("/api/v1/me/search-history/").status_code == 204
    assert SearchHistory.objects.filter(user=other).exists()


def test_search_history_keeps_latest_100(user):
    from apps.accounts.services import record_search

    for i in range(105):
        record_search(user, f"q{i}", "both", "tr")
    queries = list(
        SearchHistory.objects.filter(user=user).values_list("query", flat=True)
    )
    assert len(queries) == 100 and queries[0] == "q104" and "q4" not in queries


# ---------------------------------------------------------------------------
# Notifications & unsubscribe
# ---------------------------------------------------------------------------


def test_notifications_list_and_mark_read(signed_in, user):
    other = User.objects.create_user(email="other@example.com", password=PASSWORD)
    Notification.objects.create(user=user, kind="reminder_due", message="mine")
    Notification.objects.create(user=other, kind="reminder_due", message="theirs")
    body = signed_in.get("/api/v1/me/notifications/").json()
    assert body["unread"] == 1 and [n["message"] for n in body["results"]] == ["mine"]
    assert signed_in.post("/api/v1/me/notifications/").status_code == 204
    assert signed_in.get("/api/v1/me/notifications/").json()["unread"] == 0
    assert Notification.objects.get(user=other).read_at is None


def test_one_click_unsubscribe(api_client, user):
    response = api_client.get(
        "/api/v1/auth/unsubscribe/", {"token": unsubscribe_token(user)}
    )
    user.refresh_from_db()
    assert response.status_code == 200 and user.email_notifications is False
    assert (
        api_client.get("/api/v1/auth/unsubscribe/", {"token": "forged"}).status_code
        == 400
    )
