"""Film Notebook (plan §3.8, Faz 7B): one entry per user and title holds everything
personal about it: status, favourite, rating, private note, tags, progress.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_TAGS = 10
MAX_TAG_LENGTH = 30
MAX_NOTE_LENGTH = 5000


def validate_tags(value) -> None:
    if not isinstance(value, list) or len(value) > MAX_TAGS:
        raise ValidationError(f"Up to {MAX_TAGS} tags.")
    for tag in value:
        if not isinstance(tag, str) or not tag.strip() or len(tag) > MAX_TAG_LENGTH:
            raise ValidationError(f"Tags must be 1-{MAX_TAG_LENGTH} characters.")


class NotebookEntry(models.Model):
    class MediaType(models.TextChoices):
        MOVIE = "movie", "Movie"
        TV = "tv", "TV"

    class Status(models.TextChoices):
        WANT_TO_WATCH = "want_to_watch", "Want to watch"
        WATCHING = "watching", "Watching"
        WATCHED = "watched", "Watched"
        DROPPED = "dropped", "Dropped"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notebook"
    )
    media_type = models.CharField(max_length=5, choices=MediaType.choices)
    tmdb_id = models.PositiveIntegerField()
    status = models.CharField(
        max_length=14, choices=Status.choices, null=True, blank=True, db_index=True
    )
    is_favorite = models.BooleanField(default=False, db_index=True)
    # Stored ×2 so half stars stay exact integers: 1 = ½★ … 10 = 5★ (None = unrated).
    rating_x2 = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    # Private, plain text. Never sent to an LLM; rendered as text, never as HTML.
    note = models.TextField(blank=True, max_length=MAX_NOTE_LENGTH)
    tags = models.JSONField(default=list, blank=True, validators=[validate_tags])
    watched_on = models.DateField(null=True, blank=True)
    rewatch_count = models.PositiveSmallIntegerField(default=0)
    progress_season = models.PositiveSmallIntegerField(null=True, blank=True)
    progress_episode = models.PositiveSmallIntegerField(null=True, blank=True)

    # TMDB snapshot so the notebook and stats work while TMDB is down. Refreshed by
    # the daily job; never older than 6 months (TMDB terms), else the TMDB fields
    # are cleared while the user's own data stays.
    title = models.CharField(max_length=255, blank=True)
    original_title = models.CharField(max_length=255, blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    genres = models.JSONField(default=list, blank=True)  # logical genre names
    runtime_minutes = models.PositiveIntegerField(null=True, blank=True)  # movie
    episode_runtime = models.PositiveIntegerField(null=True, blank=True)  # series
    episode_count = models.PositiveIntegerField(null=True, blank=True)  # series
    snapshot_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "media_type", "tmdb_id"], name="uniq_notebook_entry"
            )
        ]
        ordering = ["-updated_at", "-id"]
        verbose_name_plural = "notebook entries"

    def __str__(self) -> str:
        return f"{self.user_id}: {self.media_type}:{self.tmdb_id} ({self.status})"

    @property
    def key(self) -> str:
        return f"{self.media_type}:{self.tmdb_id}"

    def watch_minutes(self) -> int:
        """Estimated minutes watched (stats): runtime, or episodes × episode length."""
        if self.media_type == self.MediaType.MOVIE:
            return (self.runtime_minutes or 0) * (1 + self.rewatch_count)
        return (self.episode_count or 0) * (self.episode_runtime or 0)
