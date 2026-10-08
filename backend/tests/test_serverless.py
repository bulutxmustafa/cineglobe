"""Plan v1.8 serverless compatibility: shared counters and the database cache.

Serverless instances share no memory, so anything counted or cached must work
when each request may land on a different process.
"""

from datetime import date

import pytest
from apps.search import cost_guard
from apps.search.models import DailyCounter
from django.core.cache import caches
from django.core.management import call_command
from django.db import connection
from django.test import override_settings

pytestmark = pytest.mark.django_db

DAY = date(2026, 10, 8)
DB_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}


def test_daily_counter_add_and_get():
    assert DailyCounter.get("k", DAY) == 0
    DailyCounter.add("k", DAY, 5)
    DailyCounter.add("k", DAY)
    assert DailyCounter.get("k", DAY) == 6
    assert DailyCounter.get("k", date(2026, 10, 9)) == 0  # per-day


def test_add_if_below_never_overshoots_the_limit():
    results = [DailyCounter.add_if_below("q", DAY, limit=3) for _ in range(5)]
    assert results == [True, True, True, False, False]
    assert DailyCounter.get("q", DAY) == 3


def test_add_if_below_is_a_single_conditional_update():
    """The check and increment must be one statement (no read-then-write race)."""
    DailyCounter.add("q", DAY, 2)
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as ctx:
        assert DailyCounter.add_if_below("q", DAY, limit=3)
    updates = [
        q["sql"]
        for q in ctx.captured_queries
        if q["sql"].lstrip().upper().startswith("UPDATE")
    ]
    assert len(updates) == 1 and '"value" <=' in updates[0].replace("`", '"')


def test_quota_state_lives_in_the_database_not_process_memory():
    assert cost_guard.consume_quota("guest:abc", 1)
    # A fresh "process" sees the same state because it reads the table.
    assert DailyCounter.objects.get(key="llm:quota:guest:abc").value == 1
    assert not cost_guard.consume_quota("guest:abc", 1)


def test_zero_limit_quota_is_always_exhausted():
    assert cost_guard.consume_quota("guest:none", 0) is False


@override_settings(CACHES=DB_CACHE)
def test_database_cache_is_shared_between_cache_instances():
    call_command("createcachetable")
    writer = caches.create_connection("default")
    reader = caches.create_connection("default")  # e.g. another function instance
    writer.set("search:v2:abc", {"results": [1, 2]}, 60)
    assert reader.get("search:v2:abc") == {"results": [1, 2]}
    cost_guard.open_circuit("gemini")


def test_cache_table_migration_creates_django_cache_table():
    with override_settings(CACHES=DB_CACHE):
        from importlib import import_module

        migration = import_module("apps.search.migrations.0003_create_cache_table")
        migration.create_cache_table(None, type("E", (), {"connection": connection})())
    assert "django_cache" in connection.introspection.table_names()


def test_llm_sdks_are_not_imported_at_startup():
    import subprocess
    import sys

    code = (
        "import os, sys, django;"
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev');"
        "os.environ['CACHE_BACKEND']='locmem';"
        "os.environ['DATABASE_URL']='sqlite:///:memory:';"
        "django.setup(); import config.urls;"
        "print('anthropic' in sys.modules, 'google.genai' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="backend",
        check=True,
    ).stdout.strip()
    assert out == "False False"


def test_quota_identity_uses_forwarded_client_ip_behind_proxy(api_client, settings):
    """Behind Vercel every request has the proxy's REMOTE_ADDR; guests must not share a quota."""
    from apps.search.views import _quota_for
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory

    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}
    factory = APIRequestFactory()

    def quota(ip):
        raw = factory.post("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=ip)
        return _quota_for(Request(raw)).identity

    assert quota("203.0.113.7") != quota("198.51.100.9")
    assert quota("203.0.113.7") == quota("203.0.113.7")


def test_spoofed_forwarded_for_is_ignored_without_trusted_proxy(settings):
    from apps.search.views import _quota_for
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory

    assert settings.REST_FRAMEWORK["NUM_PROXIES"] == 0  # local/default
    factory = APIRequestFactory()

    def quota(fake_ip):
        raw = factory.post("/", REMOTE_ADDR="203.0.113.7", HTTP_X_FORWARDED_FOR=fake_ip)
        return _quota_for(Request(raw)).identity

    assert quota("1.1.1.1") == quota("2.2.2.2")  # same real client, same quota
