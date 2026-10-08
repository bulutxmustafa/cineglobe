"""Social layer (plan §3.11, Faz 7C): profiles, lists, notebook sharing, moderation.

Privacy first: everything is private by default and every read path asks
apps.social.visibility. Free text is plain text only; URLs are stripped and a
small TR/EN word filter applies (apps.social.text).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Visibility(models.TextChoices):
    PRIVATE = "private", "Only me"
    UNLISTED = "unlisted", "Anyone with the link"
    PUBLIC = "public", "Public"


class Profile(models.Model):
    class Avatar(models.TextChoices):
        INITIAL = "initial", "Initial letter"
        POSTER = "poster", "Favourite title's poster"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # Lower-case [a-z0-9_]{3,20}: stored folded, so uniqueness is case-insensitive
    # and look-alike Unicode is impossible by construction.
    username = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=40, blank=True)
    bio = models.CharField(max_length=200, blank=True)
    avatar_kind = models.CharField(
        max_length=8, choices=Avatar.choices, default=Avatar.INITIAL
    )
    avatar_poster_path = models.CharField(max_length=255, blank=True)
    profile_visibility = models.CharField(
        max_length=8, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    show_stats = models.BooleanField(default=False)
    username_changed_at = models.DateTimeField(null=True, blank=True)
    # Moderation: hidden automatically after enough reports, until an admin decides.
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"@{self.username}"


class UserList(models.Model):
    MAX_PER_USER = 50
    MAX_ITEMS = 200

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lists"
    )
    # Random, unguessable id used in links (unlisted lists rely on it).
    slug = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=500, blank=True)
    is_ranked = models.BooleanField(default=True)
    visibility = models.CharField(
        max_length=8, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return self.title


class UserListItem(models.Model):
    user_list = models.ForeignKey(
        UserList, on_delete=models.CASCADE, related_name="items"
    )
    media_type = models.CharField(max_length=5)
    tmdb_id = models.PositiveIntegerField()
    position = models.PositiveSmallIntegerField()
    comment = models.CharField(max_length=280, blank=True)
    # TMDB snapshot for display (refreshed/cleared like the notebook's: ≤ 6 months).
    title = models.CharField(max_length=255, blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    snapshot_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_list", "position"], name="uniq_list_position"
            ),
            models.UniqueConstraint(
                fields=["user_list", "media_type", "tmdb_id"], name="uniq_list_title"
            ),
        ]


class NotebookShare(models.Model):
    class Scope(models.TextChoices):
        RATINGS = "ratings", "Status and ratings"
        RATINGS_NOTES = "ratings_notes", "Status, ratings and notes"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shares"
    )
    # Only the SHA-256 of the token is stored; the link is shown once.
    token_hash = models.CharField(max_length=64, unique=True)
    scope = models.CharField(
        max_length=14, choices=Scope.choices, default=Scope.RATINGS
    )
    statuses = models.JSONField(default=list, blank=True)  # empty = every status
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Report(models.Model):
    class Target(models.TextChoices):
        PROFILE = "profile", "Profile"
        LIST = "list", "List"

    class Reason(models.TextChoices):
        ABUSE = "abuse", "Insult / hate"
        SPAM = "spam", "Spam / advertising"
        IMPERSONATION = "impersonation", "Impersonation / fake account"
        PERSONAL_INFO = "personal_info", "Sharing personal information"
        OTHER = "other", "Other"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_made"
    )
    target_type = models.CharField(max_length=8, choices=Target.choices)
    target_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=14, choices=Reason.choices)
    details = models.CharField(max_length=200, blank=True)
    # Counted towards auto-hiding only if the reporter's account was ≥ 24 h old.
    counts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["resolved_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "target_type", "target_id"], name="uniq_report"
            )
        ]

    def __str__(self) -> str:
        return f"{self.target_type}#{self.target_id} ({self.reason})"


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_made"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="uniq_block")
        ]
