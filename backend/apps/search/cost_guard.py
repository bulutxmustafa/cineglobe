"""Cost guard for AI search (plan §3.10): pricing, daily budget, quotas, circuit breaker.

Counters live in the Django cache (Redis in production) and are keyed by the
local date in QUOTA_TIME_ZONE, so quotas and the budget reset at midnight
Europe/Istanbul. Usage rows in LLMUsageLog are the source of truth for reports.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache

from apps.search.models import LLMUsageLog
from apps.search.providers.base import LLMProvider

# USD per 1M tokens (input, output). Verify against official pricing pages before
# relying on reports: https://platform.claude.com/docs/en/about-claude/pricing and
# https://ai.google.dev/gemini-api/docs/pricing. Unknown models are priced at 0
# and logged, so reports never silently overstate cost.
PRICES_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
    "claude-sonnet-5-5": (Decimal("2.00"), Decimal("10.00")),
    "claude-opus-5-5": (Decimal("4.00"), Decimal("20.00")),
    "gemini-3.5-flash-lite": (Decimal("0.30"), Decimal("2.50")),
}

MICRO = Decimal("1000000")


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.QUOTA_TIME_ZONE)).date()


def seconds_until_local_midnight() -> int:
    now = datetime.now(ZoneInfo(settings.QUOTA_TIME_ZONE))
    midnight = datetime.combine(
        now.date() + timedelta(days=1), datetime.min.time(), now.tzinfo
    )
    return max(int((midnight - now).total_seconds()), 1)


def call_cost(
    provider: LLMProvider, model: str, input_tokens: int, output_tokens: int
) -> Decimal:
    if not provider.is_paid:
        return Decimal("0")
    price_in, price_out = PRICES_PER_MTOK.get(model, (Decimal("0"), Decimal("0")))
    return (
        Decimal(input_tokens) * price_in + Decimal(output_tokens) * price_out
    ) / MICRO


# --- Daily budget (paid providers only) -------------------------------------


def _spend_key(day: date | None = None) -> str:
    return f"llm:spend_micro_usd:{(day or local_today()).isoformat()}"


def spent_today_usd() -> Decimal:
    return Decimal(cache.get(_spend_key(), 0)) / MICRO


def budget_exhausted() -> bool:
    return spent_today_usd() >= Decimal(str(settings.LLM_DAILY_BUDGET_USD))


def _add_spend(cost: Decimal) -> None:
    micro = int((cost * MICRO).to_integral_value())
    if micro <= 0:
        return
    key = _spend_key()
    # add() is a no-op if the key exists; then incr() is atomic on Redis.
    cache.add(key, 0, seconds_until_local_midnight() + 3600)
    cache.incr(key, micro)


def record_usage(
    provider: LLMProvider,
    model: str,
    call_type: str,
    outcome: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> LLMUsageLog:
    cost = call_cost(provider, model, input_tokens, output_tokens)
    _add_spend(cost)
    return LLMUsageLog.objects.create(
        provider=provider.name,
        model=model,
        call_type=call_type,
        outcome=outcome,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
    )


# --- Daily AI search quota ---------------------------------------------------


def quota_identity(user_id: int | None, ip_address: str | None) -> tuple[str, int]:
    """Return (cache identity, daily limit). IPs are hashed; raw IPs are never stored."""
    if user_id is not None:
        return f"user:{user_id}", settings.USER_DAILY_AI_SEARCHES
    digest = hashlib.sha256(
        f"{settings.SECRET_KEY}:{ip_address or ''}".encode()
    ).hexdigest()
    return f"guest:{digest[:32]}", settings.GUEST_DAILY_AI_SEARCHES


def _quota_key(identity: str) -> str:
    return f"llm:quota:{local_today().isoformat()}:{identity}"


def quota_remaining(identity: str, limit: int) -> int:
    return max(limit - int(cache.get(_quota_key(identity), 0)), 0)


def consume_quota(identity: str, limit: int) -> bool:
    """Count one AI search; False (and nothing consumed) when the quota is used up."""
    if quota_remaining(identity, limit) <= 0:
        return False
    key = _quota_key(identity)
    cache.add(key, 0, seconds_until_local_midnight() + 3600)
    cache.incr(key)
    return True


# --- Circuit breaker ---------------------------------------------------------


def _circuit_key(provider_name: str) -> str:
    return f"llm:circuit_open:{provider_name}"


def circuit_open(provider_name: str) -> bool:
    return bool(cache.get(_circuit_key(provider_name)))


def open_circuit(provider_name: str) -> None:
    cache.set(_circuit_key(provider_name), True, settings.LLM_CIRCUIT_BREAKER_SECONDS)
