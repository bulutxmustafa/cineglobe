"""ClassicProvider: rule-based parsing with no AI, no network and no cost.

It is always the last link of the chain, so search keeps working when every
LLM is down, rate limited, over quota or over budget.
"""

from __future__ import annotations

from apps.search.fallback import parse_query_fallback
from apps.search.providers.base import LLMProvider, LLMResult, TitleBrief
from apps.search.schemas import SearchFilters


class ClassicProvider(LLMProvider):
    name = "classic"
    uses_ai = False
    is_paid = False

    def parse_query(self, query: str) -> LLMResult[SearchFilters]:
        return LLMResult(parse_query_fallback(query), model="rules")

    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> LLMResult[dict[str, str]]:
        # Empty mapping: callers keep their template reasons.
        return LLMResult({}, model="rules")
