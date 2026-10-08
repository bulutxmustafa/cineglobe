"""User accounts (plan Faz 7): optional sign-in with e-mail and password.

Accounts are optional: every discovery feature works for guests. Signing in
adds the Film Notebook, reminders and a higher daily AI-search quota.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CineGlobeUserManager(UserManager):
    """Same signature as Django's manager; `username` is generated when omitted.

    People sign in with their e-mail. `username` stays only because Django's
    auth app expects it; the public profile handle (Faz 7C) is separate.
    """

    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("An e-mail address is required.")
        email = self.normalize_email(email).lower()
        username = username or f"u_{uuid.uuid4().hex[:16]}"
        return super()._create_user(username, email, password, **extra_fields)

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(
        self, username=None, email=None, password=None, **extra_fields
    ):
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Language(models.TextChoices):
        TR = "tr", "Türkçe"
        EN = "en", "English"

    email = models.EmailField(unique=True)
    preferred_language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.TR
    )
    # Plan v1.7: accounts are 18+ by self-declaration; no birth date is stored.
    age_confirmed_at = models.DateTimeField(null=True, blank=True)
    # Global switch for reminder e-mails (one-click unsubscribe sets it to False).
    email_notifications = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CineGlobeUserManager()

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        if not self.username:
            self.username = f"u_{uuid.uuid4().hex[:16]}"
        super().save(*args, **kwargs)


class SearchHistory(models.Model):
    """A signed-in user's own search history (only they can see or delete it)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searches")
    query = models.CharField(max_length=300)
    media_type = models.CharField(max_length=5, default="both")
    language = models.CharField(max_length=2, default="tr")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    MAX_PER_USER = 100

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name_plural = "search history"

    def __str__(self) -> str:
        return f"{self.user_id}: {self.query[:40]}"


class Notification(models.Model):
    """In-app notification (first reminder channel; plan §3.7)."""

    class Kind(models.TextChoices):
        REMINDER_DUE = "reminder_due", "Reminder due"
        RELEASE_DATE_CHANGED = "release_date_changed", "Release date changed"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=24, choices=Kind.choices)
    # Rendered in the user's language when created (plan: notification language).
    message = models.CharField(max_length=300)
    media_type = models.CharField(max_length=5, blank=True)
    tmdb_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.user_id}: {self.kind}"
