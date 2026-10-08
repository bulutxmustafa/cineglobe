"""Daily job (plan §3.7, Faz 7): refresh release dates, deliver due reminders, tidy up.

Triggered once a day by Vercel Cron (Hobby allows daily jobs) through a
secret-protected endpoint, or by `manage.py run_daily_jobs`.

Idempotent: a reminder moves pending → sent in one conditional UPDATE, so a
retried or doubled run never notifies twice. Work per run is capped so the job
fits a serverless function's time limit; leftovers are picked up next day.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Notification
from apps.catalog.models import Title
from apps.catalog.tmdb_client import TMDBClient
from apps.notebook.services import refresh_snapshots
from apps.reminders.models import Reminder
from apps.reminders.services import due_reminders, refresh_release_dates
from apps.search.models import DailyCounter
from apps.upcoming.service import local_today

logger = logging.getLogger(__name__)

REFRESH_BATCH = 150
COUNTER_RETENTION_DAYS = 35
NOTIFICATION_RETENTION_DAYS = 90
# TMDB terms: cached/stored TMDB data must not be older than 6 months.
TMDB_DATA_MAX_AGE_DAYS = 182

MESSAGES = {
    "due": {
        "tr": "Hatırlatma: {title} {when}.",
        "en": "Reminder: {title} {when}.",
    },
    "when": {
        "tr": {
            "release_day": "bugün çıkıyor",
            "one_day_before": "yarın çıkıyor",
            "one_week_before": "bir hafta sonra çıkıyor",
        },
        "en": {
            "release_day": "is out today",
            "one_day_before": "comes out tomorrow",
            "one_week_before": "comes out in a week",
        },
    },
    "moved": {
        "tr": "{title} için çıkış tarihi değişti: {date}.",
        "en": "{title} has a new release date: {date}.",
    },
    "moved_unknown": {
        "tr": "{title} için çıkış tarihi artık belirsiz.",
        "en": "{title} no longer has an announced release date.",
    },
}


@dataclass
class DailyReport:
    refreshed: int = 0
    date_changes: int = 0
    sent: int = 0
    emails: int = 0
    counters_purged: int = 0
    notifications_purged: int = 0
    stale_titles_purged: int = 0
    snapshots_refreshed: int = 0
    snapshots_cleared: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def _language(user) -> str:
    return user.preferred_language if user.preferred_language in ("tr", "en") else "tr"


def _title(reminder: Reminder) -> str:
    return reminder.title or f"#{reminder.tmdb_id}"


def notify_date_change(reminder: Reminder) -> None:
    language = _language(reminder.user)
    if reminder.last_known_release_date:
        message = MESSAGES["moved"][language].format(
            title=_title(reminder), date=reminder.last_known_release_date.isoformat()
        )
    else:
        message = MESSAGES["moved_unknown"][language].format(title=_title(reminder))
    Notification.objects.create(
        user=reminder.user,
        kind=Notification.Kind.RELEASE_DATE_CHANGED,
        message=message,
        media_type=reminder.media_type,
        tmdb_id=reminder.tmdb_id,
    )


def deliver(reminder: Reminder) -> tuple[bool, bool]:
    """Send one due reminder. Returns (sent, emailed); sent=False if already done."""
    claimed = Reminder.objects.filter(
        pk=reminder.pk, status=Reminder.Status.PENDING
    ).update(status=Reminder.Status.SENT, sent_at=timezone.now())
    if not claimed:
        return False, False  # another run got it first: never notify twice

    user = reminder.user
    language = _language(user)
    when = MESSAGES["when"][language][reminder.remind_on]
    message = MESSAGES["due"][language].format(title=_title(reminder), when=when)
    if "in_app" in reminder.channels or not settings.EMAIL_ENABLED:
        Notification.objects.create(
            user=user,
            kind=Notification.Kind.REMINDER_DUE,
            message=message,
            media_type=reminder.media_type,
            tmdb_id=reminder.tmdb_id,
        )

    emailed = False
    if (
        "email" in reminder.channels
        and settings.EMAIL_ENABLED
        and user.email_notifications
    ):
        from apps.accounts.views import unsubscribe_token

        unsubscribe = f"{settings.SITE_URL}/api/v1/auth/unsubscribe/?token={unsubscribe_token(user)}"
        footer = {
            "tr": f"\n\nHatırlatma e-postalarını kapatmak için: {unsubscribe}",
            "en": f"\n\nTurn off reminder e-mails: {unsubscribe}",
        }[language]
        try:
            send_mail("CineGlobe", message + footer, None, [user.email])
            emailed = True
        except Exception:  # noqa: BLE001 - a mail outage must not fail the whole job
            logger.exception("Reminder e-mail failed for reminder %s", reminder.pk)
    return True, emailed


def purge_stale_tmdb_titles(today: date) -> int:
    """Delete stored TMDB titles older than 6 months; they are re-fetched on demand."""
    cutoff = timezone.now() - timedelta(days=TMDB_DATA_MAX_AGE_DAYS)
    # cached_at is refreshed whenever the title is fetched again; TVDetails cascade.
    deleted, _ = Title.objects.filter(cached_at__lt=cutoff).delete()
    return deleted


def run_daily(
    today: date | None = None, client: TMDBClient | None = None
) -> DailyReport:
    today = today or local_today()
    report = DailyReport()

    pending = list(
        Reminder.objects.filter(status=Reminder.Status.PENDING)
        .select_related("user")
        .order_by("updated_at")[:REFRESH_BATCH]
    )
    if pending:
        try:
            tmdb = client or TMDBClient()
        except ValueError:
            tmdb = None
            logger.warning("TMDB_API_KEY missing: release dates not refreshed today")
        if tmdb is not None:
            changed = refresh_release_dates(pending, tmdb)
            report.refreshed = len(pending)
            report.date_changes = len(changed)
            for reminder in changed:
                notify_date_change(reminder)

    for reminder in due_reminders(today):
        sent, emailed = deliver(reminder)
        report.sent += int(sent)
        report.emails += int(emailed)

    report.counters_purged, _ = DailyCounter.objects.filter(
        day__lt=today - timedelta(days=COUNTER_RETENTION_DAYS)
    ).delete()
    report.notifications_purged, _ = Notification.objects.filter(
        Q(read_at__isnull=False)
        & Q(created_at__lt=timezone.now() - timedelta(days=NOTIFICATION_RETENTION_DAYS))
    ).delete()
    report.stale_titles_purged = purge_stale_tmdb_titles(today)
    try:
        snapshot_client = client or TMDBClient()
    except ValueError:
        snapshot_client = None
    snapshots = refresh_snapshots(snapshot_client)
    report.snapshots_refreshed = snapshots["refreshed"]
    report.snapshots_cleared = snapshots["cleared"]
    logger.info("Daily job: %s", report.as_dict())
    return report
