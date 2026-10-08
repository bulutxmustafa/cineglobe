"""Admin cost view for LLM usage (plan §3.10)."""

from decimal import Decimal

import pytest
from apps.search.models import LLMUsageLog
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def test_usage_admin_shows_today_and_month_totals(client):
    admin = get_user_model().objects.create_superuser(
        "root", "r@example.com", "pw-123456"
    )
    client.force_login(admin)
    LLMUsageLog.objects.create(
        provider="anthropic",
        model="claude-haiku-5-5",
        call_type="parse",
        outcome="ok",
        input_tokens=2400,
        output_tokens=700,
        cost_usd=Decimal("0.00059"),
    )
    LLMUsageLog.objects.create(
        provider="gemini", model="-", call_type="parse", outcome="unavailable"
    )

    response = client.get("/admin/search/llmusagelog/")

    assert response.status_code == 200
    today = response.context["usage_today"]
    assert (today["calls"], today["failed"]) == (2, 1)
    assert today["cost_usd"] == Decimal("0.00059")
    assert response.context["usage_month"]["calls"] == 2
    assert b"Daily budget (paid providers)" in response.content
    assert str(LLMUsageLog.objects.first())


def test_usage_log_is_read_only_in_admin(client):
    admin = get_user_model().objects.create_superuser(
        "root", "r@example.com", "pw-123456"
    )
    client.force_login(admin)
    assert client.get("/admin/search/llmusagelog/add/").status_code == 403
