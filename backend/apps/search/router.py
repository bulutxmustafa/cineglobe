"""LLMRouter: run the provider chain with circuit breaker, budget, quota and usage logging.

Search never fails because of an LLM. Whatever happens (no key, 429, timeout,
invalid JSON, quota or budget exhausted) the classic rule-based provider answers
and `ai_status` tells the client why.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from apps.search import cost_guard
from apps.search.models import LLMUsageLog
from apps.search.providers import build_chain
from apps.search.providers.base import (
    LLMProvider,
    LLMResult,
    ProviderError,
    ProviderOutputError,
    ProviderUnavailableError,
    TitleBrief,
)
from apps.search.schemas import SearchFilters

logger = logging.getLogger(__name__)

AIStatus = Literal["ok", "quota_exceeded", "budget_exceeded", "fallback"]
# One retry after invalid output (plan §3.10), none after transient failures:
# those open the circuit breaker and move on to the next provider.
OUTPUT_RETRIES = 1


@dataclass(frozen=True)
class ParseOutcome:
    filters: SearchFilters
    provider: str
    ai_status: AIStatus
    #: False when the result came from a degraded path that may succeed later.
    cacheable: bool


@dataclass(frozen=True)
class Quota:
    identity: str
    limit: int


class LLMRouter:
    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        self.providers = providers if providers is not None else build_chain()
        self._classic = next(p for p in reversed(self.providers) if not p.uses_ai)

    # ------------------------------------------------------------------

    def parse(self, query: str, quota: Quota | None = None) -> ParseOutcome:
        ai_providers = [p for p in self.providers if p.uses_ai and p.is_configured()]
        if not ai_providers:
            # Classic-only deployment: deterministic, safe to cache.
            return self._classic_outcome(query, "fallback", cacheable=True)

        candidates, budget_blocked = self._candidates(ai_providers)
        if not candidates:
            status: AIStatus = "budget_exceeded" if budget_blocked else "fallback"
            return self._classic_outcome(query, status, cacheable=False)

        if quota is not None and not cost_guard.consume_quota(
            quota.identity, quota.limit
        ):
            return self._classic_outcome(query, "quota_exceeded", cacheable=False)

        for provider in candidates:
            result = self._run(
                provider,
                LLMUsageLog.CallType.PARSE,
                lambda p=provider: p.parse_query(query),
            )
            if result is not None:
                return ParseOutcome(result.value, provider.name, "ok", cacheable=True)

        return self._classic_outcome(query, "fallback", cacheable=False)

    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> dict[str, str]:
        """LLM reasons for the given titles; {} when no provider can answer."""
        if not titles:
            return {}
        ai_providers = [p for p in self.providers if p.uses_ai and p.is_configured()]
        candidates, _ = self._candidates(ai_providers)
        for provider in candidates:
            result = self._run(
                provider,
                LLMUsageLog.CallType.EXPLAIN,
                lambda p=provider: p.explain(titles, query, language),
                retries=0,
            )
            if result is not None:
                valid_keys = {t.key for t in titles}
                # Ignore keys the model invented.
                return {k: v for k, v in result.value.items() if k in valid_keys}
        return {}

    # ------------------------------------------------------------------

    def _candidates(
        self, providers: list[LLMProvider]
    ) -> tuple[list[LLMProvider], bool]:
        candidates: list[LLMProvider] = []
        budget_blocked = False
        for provider in providers:
            if cost_guard.circuit_open(provider.name):
                continue
            if provider.is_paid and cost_guard.budget_exhausted():
                budget_blocked = True
                continue
            candidates.append(provider)
        return candidates, budget_blocked

    def _classic_outcome(
        self, query: str, status: AIStatus, *, cacheable: bool
    ) -> ParseOutcome:
        filters = self._classic.parse_query(query).value
        return ParseOutcome(filters, self._classic.name, status, cacheable)

    def _run(
        self,
        provider: LLMProvider,
        call_type: str,
        call: Callable[[], LLMResult],
        retries: int = OUTPUT_RETRIES,
    ) -> LLMResult | None:
        for attempt in range(retries + 1):
            try:
                result = call()
            except ProviderUnavailableError as exc:
                logger.warning("LLM provider %s unavailable: %s", provider.name, exc)
                cost_guard.open_circuit(provider.name)
                self._log(provider, call_type, LLMUsageLog.Outcome.UNAVAILABLE)
                return None
            except ProviderOutputError as exc:
                logger.warning(
                    "LLM provider %s bad output (attempt %d): %s",
                    provider.name,
                    attempt + 1,
                    exc,
                )
                self._log(provider, call_type, LLMUsageLog.Outcome.BAD_OUTPUT)
                continue
            except ProviderError as exc:
                logger.error("LLM provider %s error: %s", provider.name, exc)
                self._log(provider, call_type, LLMUsageLog.Outcome.ERROR)
                return None

            cost_guard.record_usage(
                provider,
                result.model,
                call_type,
                LLMUsageLog.Outcome.OK,
                result.input_tokens,
                result.output_tokens,
            )
            return result
        return None

    @staticmethod
    def _log(provider: LLMProvider, call_type: str, outcome: str) -> None:
        cost_guard.record_usage(provider, "-", call_type, outcome)
