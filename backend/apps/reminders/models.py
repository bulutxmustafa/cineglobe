"""Release reminders (plan §3.7). Delivery (in-app/e-mail) is wired up in Faz 7."""

from __future__ import annotations

from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

CHANNELS = ("in_app", "email", "push")


def validate_channels(value) -> None:
    if (
        not isinstance(value, list)
        or not value
        or not all(v in CHANNELS for v in value)
        or len(set(value)) != len(value)
    ):
        raise ValidationError(
            f"Choose one or more of {', '.join(CHANNELS)} (no repeats)."
        )


def default_channels() -> list[str]:
    return ["in_app"]


class Reminder(models.Model):
    class MediaType(models.TextChoices):
        MOVIE = "movie", "Movie"
        TV = "tv", "TV"

    class RemindOn(models.TextChoices):
        RELEASE_DAY = "release_day", "On release day"
        ONE_DAY_BEFORE = "one_day_before", "One day before"
        ONE_WEEK_BEFORE = "one_week_before", "One week before"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        CANCELLED = "cancelled", "Cancelled"

    OFFSETS = {
        RemindOn.RELEASE_DAY: timedelta(0),
        RemindOn.ONE_DAY_BEFORE: timedelta(days=1),
        RemindOn.ONE_WEEK_BEFORE: timedelta(days=7),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    media_type = models.CharField(max_length=5, choices=MediaType.choices)
    tmdb_id = models.PositiveIntegerField()
    # Snapshot so the reminder list renders without TMDB; refreshed by the daily job.
    title = models.CharField(max_length=200, blank=True)
    # Series only: the season whose premiere is awaited (None for a new series' start).
    season_number = models.PositiveSmallIntegerField(null=True, blank=True)
    remind_on = models.CharField(
        max_length=16, choices=RemindOn.choices, default=RemindOn.RELEASE_DAY
    )
    channels = models.JSONField(
        default=default_channels, validators=[validate_channels]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    last_known_release_date = models.DateField(null=True, blank=True)
    # Set when the daily job sees the date move, so the user can be told (plan §3.7).
    release_date_changed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "media_type", "tmdb_id"], name="uniq_reminder_per_title"
            )
        ]
        ordering = ["last_known_release_date", "id"]

    def __str__(self) -> str:
        return f"{self.user} → {self.media_type}:{self.tmdb_id} ({self.status})"

    def due_date(self) -> date | None:
        if self.last_known_release_date is None:
            return None
        return self.last_known_release_date - self.OFFSETS[self.remind_on]
