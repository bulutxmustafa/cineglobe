"""Faz 4C tests: Reminder model and service layer (delivery comes in Faz 7)."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from apps.catalog.tmdb_client import TMDBNotFoundError, TMDBServiceUnavailableError
from apps.reminders.models import Reminder
from apps.reminders.services import (
    ReminderError,
    cancel_reminder,
    create_reminder,
    due_reminders,
    refresh_release_dates,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

pytestmark = pytest.mark.django_db
TODAY = date(2026, 10, 8)


@pytest.fixture(autouse=True)
def _today():
    with patch("apps.reminders.services.local_today", return_value=TODAY):
        yield


@pytest.fixture
def user():
    return get_user_model().objects.create_user("ada", "ada@example.com", "pw-123456")


def tmdb(movie_date="2026-12-16", tr_dates=("2026-12-18",), tv=None):
    client = MagicMock()
    client.get_movie_detail.return_value = {
        "title": "Big Film",
        "release_date": movie_date,
    }
    client.get_movie_release_dates.return_value = {
        "results": [
            {
                "iso_3166_1": "US",
                "release_dates": [
                    {"type": 3, "release_date": "2026-12-16T00:00:00.000Z"}
                ],
            },
            {
                "iso_3166_1": "TR",
                "release_dates": [
                    {"type": 3, "release_date": f"{d}T00:00:00.000Z"} for d in tr_dates
                ]
                + [
                    {"type": 4, "release_date": "2027-03-01T00:00:00.000Z"}
                ],  # digital: ignored
            },
        ]
    }
    client.get_tv_detail.return_value = tv or {
        "name": "Show",
        "first_air_date": "2008-01-20",
        "next_episode_to_air": {
            "air_date": "2026-11-05",
            "season_number": 6,
            "episode_number": 1,
        },
    }
    return client


def test_movie_reminder_uses_turkish_theatrical_date(user):
    reminder, created = create_reminder(
        user, media_type="movie", tmdb_id=1, client=tmdb()
    )
    assert created
    assert reminder.last_known_release_date == date(2026, 12, 18)
    assert (reminder.title, reminder.status, reminder.channels) == (
        "Big Film",
        "pending",
        ["in_app"],
    )


def test_movie_without_turkish_date_falls_back_to_global(user):
    reminder, _ = create_reminder(
        user, media_type="movie", tmdb_id=1, client=tmdb(tr_dates=())
    )
    assert reminder.last_known_release_date == date(2026, 12, 16)


def test_series_reminder_targets_next_season_premiere(user):
    reminder, _ = create_reminder(user, media_type="tv", tmdb_id=2, client=tmdb())
    assert (reminder.last_known_release_date, reminder.season_number) == (
        date(2026, 11, 5),
        6,
    )


def test_new_series_premiere(user):
    client = tmdb(tv={"name": "New", "first_air_date": "2026-10-20"})
    reminder, _ = create_reminder(user, media_type="tv", tmdb_id=3, client=client)
    assert (reminder.last_known_release_date, reminder.season_number) == (
        date(2026, 10, 20),
        1,
    )


def test_series_mid_season_has_nothing_to_remind(user):
    client = tmdb(
        tv={
            "name": "S",
            "first_air_date": "2008-01-01",
            "next_episode_to_air": {
                "air_date": "2026-10-10",
                "season_number": 3,
                "episode_number": 4,
            },
        }
    )
    with pytest.raises(ReminderError) as err:
        create_reminder(user, media_type="tv", tmdb_id=4, client=client)
    assert err.value.code == "no_upcoming_season"


def test_released_title_cannot_get_a_reminder(user):
    with pytest.raises(ReminderError) as err:
        create_reminder(
            user, media_type="movie", tmdb_id=1, client=tmdb(tr_dates=("2026-10-07",))
        )
    assert err.value.code == "already_released"


def test_release_day_itself_is_allowed(user):
    reminder, _ = create_reminder(
        user, media_type="movie", tmdb_id=1, client=tmdb(tr_dates=("2026-10-08",))
    )
    assert reminder.due_date() == TODAY


def test_unknown_title(user):
    client = tmdb()
    client.get_movie_detail.side_effect = TMDBNotFoundError("x")
    with pytest.raises(ReminderError) as err:
        create_reminder(user, media_type="movie", tmdb_id=9, client=client)
    assert err.value.code == "title_not_found"


def test_no_duplicates_second_request_updates_and_reactivates(user):
    first, created = create_reminder(user, media_type="movie", tmdb_id=1, client=tmdb())
    cancel_reminder(first)
    second, created_again = create_reminder(
        user,
        media_type="movie",
        tmdb_id=1,
        remind_on="one_week_before",
        channels=["in_app", "email"],
        client=tmdb(),
    )
    assert created and not created_again
    assert second.pk == first.pk and Reminder.objects.count() == 1
    assert (second.status, second.remind_on, second.channels) == (
        "pending",
        "one_week_before",
        ["in_app", "email"],
    )


def test_unique_constraint_in_database(user):
    Reminder.objects.create(user=user, media_type="movie", tmdb_id=1)
    with pytest.raises(IntegrityError):
        Reminder.objects.create(user=user, media_type="movie", tmdb_id=1)


def test_same_id_movie_and_series_are_separate_reminders(user):
    create_reminder(user, media_type="movie", tmdb_id=550, client=tmdb())
    create_reminder(user, media_type="tv", tmdb_id=550, client=tmdb())
    assert Reminder.objects.count() == 2


@pytest.mark.parametrize("channels", [[], ["sms"], ["email", "email"], "email"])
def test_invalid_channels_are_rejected(user, channels):
    with pytest.raises(ValidationError):
        Reminder(
            user=user, media_type="movie", tmdb_id=1, channels=channels
        ).full_clean()


def test_service_validates_channels(user):
    with pytest.raises(ValidationError):
        create_reminder(
            user, media_type="movie", tmdb_id=1, channels=["sms"], client=tmdb()
        )
    assert not Reminder.objects.exists()


@pytest.mark.parametrize(
    "remind_on, due",
    [
        ("release_day", date(2026, 12, 18)),
        ("one_day_before", date(2026, 12, 17)),
        ("one_week_before", date(2026, 12, 11)),
    ],
)
def test_due_date_offsets(user, remind_on, due):
    reminder, _ = create_reminder(
        user, media_type="movie", tmdb_id=1, remind_on=remind_on, client=tmdb()
    )
    assert reminder.due_date() == due


def test_due_reminders_selects_pending_only(user):
    due, _ = create_reminder(
        user, media_type="movie", tmdb_id=1, client=tmdb(tr_dates=("2026-10-08",))
    )
    later, _ = create_reminder(user, media_type="movie", tmdb_id=2, client=tmdb())
    cancelled, _ = create_reminder(
        user, media_type="movie", tmdb_id=3, client=tmdb(tr_dates=("2026-10-08",))
    )
    cancel_reminder(cancelled)
    assert due_reminders(TODAY) == [due]


def test_refresh_detects_moved_release_dates_and_survives_tmdb_errors(user):
    moved, _ = create_reminder(user, media_type="movie", tmdb_id=1, client=tmdb())
    steady, _ = create_reminder(user, media_type="movie", tmdb_id=2, client=tmdb())
    client = tmdb(tr_dates=("2027-01-15",))
    client.get_movie_detail.side_effect = [
        {"title": "Big Film", "release_date": "2026-12-16"},
        TMDBServiceUnavailableError("down"),
    ]
    changed = refresh_release_dates([moved, steady], client)
    assert changed == [moved]
    moved.refresh_from_db()
    steady.refresh_from_db()
    assert (
        moved.last_known_release_date == date(2027, 1, 15)
        and moved.release_date_changed_at
    )
    assert steady.last_known_release_date == date(2026, 12, 18)  # kept on TMDB error
