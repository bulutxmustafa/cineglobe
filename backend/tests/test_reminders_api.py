"""Faz 7 tests: reminder endpoints, the daily job and the cron trigger."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from apps.accounts.models import Notification
from apps.catalog.models import Title
from apps.reminders.jobs import run_daily
from apps.reminders.models import Reminder
from apps.search.models import DailyCounter
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
User = get_user_model()
TODAY = date(2026, 10, 8)


@pytest.fixture(autouse=True)
def _today():
    with (
        patch("apps.reminders.services.local_today", return_value=TODAY),
        patch("apps.reminders.jobs.local_today", return_value=TODAY),
    ):
        yield


def tmdb(tr_date="2026-12-18"):
    client = MagicMock()
    client.get_movie_detail.return_value = {
        "title": "Big Film",
        "release_date": "2026-12-16",
    }
    client.get_movie_release_dates.return_value = {
        "results": [
            {
                "iso_3166_1": "TR",
                "release_dates": [
                    {"type": 3, "release_date": f"{tr_date}T00:00:00.000Z"}
                ],
            }
        ]
    }
    client.get_tv_detail.return_value = {
        "name": "Show",
        "first_air_date": "2008-01-20",
        "next_episode_to_air": {
            "air_date": "2026-11-05",
            "season_number": 6,
            "episode_number": 1,
        },
    }
    return client


def dated_tmdb():
    """TMDB double that reports each reminder's stored date (nothing moved)."""
    client = MagicMock()

    def detail(tmdb_id, language="tr-TR"):
        stored = Reminder.objects.filter(tmdb_id=tmdb_id).first()
        release = stored.last_known_release_date.isoformat() if stored else ""
        return {"title": f"Film {tmdb_id}", "release_date": release}

    client.get_movie_detail.side_effect = detail
    client.get_movie_release_dates.return_value = {"results": []}
    return client


@pytest.fixture
def fake_tmdb():
    client = tmdb()
    with patch("apps.reminders.views.TMDBClient", return_value=client):
        yield client


def make_user(email="ada@example.com", language="tr"):
    return User.objects.create_user(
        email=email, password="x", preferred_language=language
    )


@pytest.fixture
def client_for():
    def build(user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    return build


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def test_create_list_and_duplicate(client_for, fake_tmdb):
    client = client_for(make_user())
    first = client.post(
        "/api/v1/reminders/", {"media_type": "movie", "tmdb_id": 1}, format="json"
    )
    again = client.post(
        "/api/v1/reminders/",
        {"media_type": "movie", "tmdb_id": 1, "remind_on": "one_day_before"},
        format="json",
    )
    assert first.status_code == 201 and again.status_code == 200
    assert first.json()["id"] == again.json()["id"]
    listing = client.get("/api/v1/reminders/").json()
    assert len(listing) == 1 and listing[0]["due_date"] == "2026-12-17"


def test_create_errors(client_for, fake_tmdb):
    client = client_for(make_user())
    fake_tmdb.get_movie_release_dates.return_value = {
        "results": [
            {
                "iso_3166_1": "TR",
                "release_dates": [
                    {"type": 3, "release_date": "2026-01-01T00:00:00.000Z"}
                ],
            }
        ]
    }
    released = client.post(
        "/api/v1/reminders/", {"media_type": "movie", "tmdb_id": 1}, format="json"
    )
    assert (
        released.status_code == 400
        and released.json()["error"]["code"] == "already_released"
    )
    bad_channel = client.post(
        "/api/v1/reminders/",
        {"media_type": "movie", "tmdb_id": 1, "channels": ["sms"]},
        format="json",
    )
    assert bad_channel.status_code == 400


def test_cannot_touch_someone_elses_reminder(client_for, fake_tmdb):
    owner, intruder = make_user(), make_user("eve@example.com")
    reminder = Reminder.objects.create(user=owner, media_type="movie", tmdb_id=1)
    attacker = client_for(intruder)
    assert attacker.get("/api/v1/reminders/").json() == []
    assert attacker.delete(f"/api/v1/reminders/{reminder.pk}/").status_code == 404
    reminder.refresh_from_db()
    assert reminder.status == "pending"


def test_cancel_hides_from_list(client_for, fake_tmdb):
    user = make_user()
    client = client_for(user)
    reminder_id = client.post(
        "/api/v1/reminders/", {"media_type": "tv", "tmdb_id": 2}, format="json"
    ).json()["id"]
    assert client.delete(f"/api/v1/reminders/{reminder_id}/").status_code == 204
    assert client.get("/api/v1/reminders/").json() == []
    assert Reminder.objects.get().status == "cancelled"


def test_bulk_hand_over_after_sign_in(client_for, fake_tmdb):
    client = client_for(make_user())
    fake_tmdb.get_movie_release_dates.side_effect = [
        {
            "results": [
                {
                    "iso_3166_1": "TR",
                    "release_dates": [
                        {"type": 3, "release_date": "2026-12-18T00:00:00.000Z"}
                    ],
                }
            ]
        },
        {
            "results": [
                {
                    "iso_3166_1": "TR",
                    "release_dates": [
                        {"type": 3, "release_date": "2020-01-01T00:00:00.000Z"}
                    ],
                }
            ]
        },
    ]
    response = client.post(
        "/api/v1/reminders/bulk/",
        {
            "items": [
                {"media_type": "movie", "tmdb_id": 1},
                {"media_type": "movie", "tmdb_id": 2},
                {"media_type": "tv", "tmdb_id": 3},
            ]
        },
        format="json",
    )
    body = response.json()
    assert [r["tmdb_id"] for r in body["created"]] == [1, 3]
    assert body["skipped"] == [
        {"media_type": "movie", "tmdb_id": 2, "code": "already_released"}
    ]


# ---------------------------------------------------------------------------
# Daily job
# ---------------------------------------------------------------------------


def reminder(
    user, tmdb_id, release, remind_on="release_day", status="pending", channels=None
):
    return Reminder.objects.create(
        user=user,
        media_type="movie",
        tmdb_id=tmdb_id,
        title=f"Film {tmdb_id}",
        remind_on=remind_on,
        status=status,
        last_known_release_date=release,
        channels=channels or ["in_app"],
    )


def test_sends_on_the_right_day_only_once_and_skips_cancelled():
    ada = make_user()
    due_today = reminder(ada, 1, TODAY)
    week_before = reminder(ada, 2, TODAY + timedelta(days=7), "one_week_before")
    tomorrow = reminder(ada, 3, TODAY + timedelta(days=1))
    reminder(ada, 4, TODAY, status="cancelled")

    report = run_daily(client=dated_tmdb())
    assert report.sent == 2
    sent = set(Reminder.objects.filter(status="sent").values_list("pk", flat=True))
    assert sent == {due_today.pk, week_before.pk}
    assert Reminder.objects.get(pk=tomorrow.pk).status == "pending"

    again = run_daily(client=dated_tmdb())  # e.g. cron retried
    assert again.sent == 0
    assert Notification.objects.filter(kind="reminder_due").count() == 2


def test_notification_language_follows_user():
    reminder(make_user("tr@example.com", "tr"), 1, TODAY)
    reminder(make_user("en@example.com", "en"), 2, TODAY, "one_day_before")
    Reminder.objects.filter(tmdb_id=2).update(
        last_known_release_date=TODAY + timedelta(days=1)
    )
    run_daily(client=dated_tmdb())
    messages = dict(Notification.objects.values_list("user__email", "message"))
    assert messages["tr@example.com"] == "Hatırlatma: Film 1 bugün çıkıyor."
    assert messages["en@example.com"] == "Reminder: Film 2 comes out tomorrow."


def test_release_date_change_updates_and_notifies():
    user = make_user()
    moved = reminder(user, 1, date(2026, 12, 18))
    report = run_daily(client=tmdb(tr_date="2027-01-15"))
    moved.refresh_from_db()
    assert report.date_changes == 1
    assert moved.last_known_release_date == date(2027, 1, 15)
    assert Notification.objects.get(kind="release_date_changed").message == (
        "Film 1 için çıkış tarihi değişti: 2027-01-15."
    )


def test_email_channel_only_when_enabled_and_allowed(settings):
    settings.EMAIL_ENABLED = True
    settings.SITE_URL = "https://cineglobe.example"
    yes = make_user("yes@example.com")
    no = make_user("no@example.com")
    no.email_notifications = False
    no.save()
    reminder(yes, 1, TODAY, channels=["email"])
    reminder(no, 2, TODAY, channels=["email"])
    report = run_daily(client=dated_tmdb())
    assert report.emails == 1 and [m.to for m in mail.outbox] == [["yes@example.com"]]
    assert "/api/v1/auth/unsubscribe/?token=" in mail.outbox[0].body


def test_email_only_reminder_falls_back_to_in_app_when_email_is_off(settings):
    settings.EMAIL_ENABLED = False
    reminder(make_user(), 1, TODAY, channels=["email"])
    run_daily(client=dated_tmdb())
    assert (
        Notification.objects.filter(kind="reminder_due").count() == 1
        and not mail.outbox
    )


def test_housekeeping_purges_old_counters_and_six_month_old_tmdb_data():
    DailyCounter.objects.create(key="k", day=TODAY - timedelta(days=40), value=1)
    DailyCounter.objects.create(key="k", day=TODAY, value=1)
    old = Title.objects.create(media_type="movie", tmdb_id=1, title="Old")
    Title.objects.filter(pk=old.pk).update(
        cached_at=timezone.now() - timedelta(days=200)
    )
    Title.objects.create(media_type="movie", tmdb_id=2, title="Fresh")
    report = run_daily(client=dated_tmdb())
    assert report.counters_purged == 1 and DailyCounter.objects.count() == 1
    assert list(Title.objects.values_list("tmdb_id", flat=True)) == [2]


# ---------------------------------------------------------------------------
# Cron endpoint
# ---------------------------------------------------------------------------


def test_cron_endpoint_requires_the_secret(api_client, settings):
    settings.CRON_SECRET = "s3cret-value"
    assert api_client.get("/api/v1/cron/daily/").status_code == 404
    assert (
        api_client.get(
            "/api/v1/cron/daily/", HTTP_AUTHORIZATION="Bearer wrong"
        ).status_code
        == 404
    )
    ok = api_client.get("/api/v1/cron/daily/", HTTP_AUTHORIZATION="Bearer s3cret-value")
    assert ok.status_code == status.HTTP_200_OK and "sent" in ok.json()


def test_cron_endpoint_disabled_without_a_secret(api_client, settings):
    settings.CRON_SECRET = ""
    assert (
        api_client.get("/api/v1/cron/daily/", HTTP_AUTHORIZATION="Bearer ").status_code
        == 404
    )


def test_management_command(capsys):
    from django.core.management import call_command

    with patch("apps.reminders.jobs.TMDBClient", return_value=tmdb()):
        call_command("run_daily_jobs")
    assert '"sent": 0' in capsys.readouterr().out


def test_postponed_release_is_not_reminded_on_the_old_date():
    """Dates are refreshed before sending: a film moved later must not ping today."""
    user = make_user()
    postponed = reminder(user, 1, TODAY)
    report = run_daily(client=tmdb(tr_date="2026-11-20"))
    postponed.refresh_from_db()
    assert report.sent == 0 and postponed.status == "pending"
    assert postponed.last_known_release_date == date(2026, 11, 20)
    assert Notification.objects.get().kind == "release_date_changed"
