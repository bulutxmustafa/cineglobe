"""Account services: data export and deletion (KVKK/GDPR basics, plan Faz 7)."""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import transaction

from apps.accounts.models import Notification, SearchHistory


def export_user_data(user: AbstractBaseUser) -> dict[str, Any]:
    """Everything stored about the user, as JSON-ready data (right of access/portability).

    Sections from later phases (notebook, lists, shares) register themselves via
    `EXPORT_SECTIONS` so this stays the single export entry point.
    """
    data: dict[str, Any] = {
        "account": {
            "email": user.email,
            "preferred_language": user.preferred_language,
            "email_notifications": user.email_notifications,
            "date_joined": user.date_joined.isoformat(),
            "age_confirmed_at": (
                user.age_confirmed_at.isoformat() if user.age_confirmed_at else None
            ),
        },
        "search_history": [
            {
                "query": s.query,
                "media_type": s.media_type,
                "language": s.language,
                "created_at": s.created_at.isoformat(),
            }
            for s in SearchHistory.objects.filter(user=user)
        ],
        "notifications": [
            {
                "kind": n.kind,
                "message": n.message,
                "created_at": n.created_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
            }
            for n in Notification.objects.filter(user=user)
        ],
    }
    for section, builder in EXPORT_SECTIONS.items():
        data[section] = builder(user)
    return data


def _reminders(user) -> list[dict[str, Any]]:
    Reminder = apps.get_model("reminders", "Reminder")
    return [
        {
            "media_type": r.media_type,
            "tmdb_id": r.tmdb_id,
            "title": r.title,
            "remind_on": r.remind_on,
            "channels": r.channels,
            "status": r.status,
            "release_date": (
                r.last_known_release_date.isoformat()
                if r.last_known_release_date
                else None
            ),
        }
        for r in Reminder.objects.filter(user=user)
    ]


EXPORT_SECTIONS: dict[str, Any] = {"reminders": _reminders}


def delete_account(user: AbstractBaseUser) -> None:
    """Permanently delete the user; related rows go with it (FK CASCADE)."""
    with transaction.atomic():
        user.delete()


def record_search(user, query: str, media_type: str, language: str) -> None:
    """Keep the signed-in user's last MAX_PER_USER searches."""
    if not user or not user.is_authenticated:
        return
    SearchHistory.objects.create(
        user=user, query=query[:300], media_type=media_type, language=language
    )
    stale = SearchHistory.objects.filter(user=user).values_list("id", flat=True)[
        SearchHistory.MAX_PER_USER :
    ]
    if stale:
        SearchHistory.objects.filter(id__in=list(stale)).delete()
