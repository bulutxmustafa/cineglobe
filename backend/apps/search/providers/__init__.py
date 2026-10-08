"""LLM provider registry: build the configured chain from LLM_PROVIDER_CHAIN."""

from __future__ import annotations

import logging

from django.conf import settings

from apps.search.providers.anthropic import AnthropicProvider
from apps.search.providers.base import LLMProvider
from apps.search.providers.classic import ClassicProvider
from apps.search.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)

PROVIDERS: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
    "classic": ClassicProvider,
}


def build_chain(names: list[str] | None = None) -> list[LLMProvider]:
    """Instantiate providers in order; unknown names are skipped, classic is always last."""
    chain: list[LLMProvider] = []
    for name in names if names is not None else settings.LLM_PROVIDER_CHAIN:
        cls = PROVIDERS.get(name)
        if cls is None:
            logger.warning(
                "Unknown LLM provider %r in LLM_PROVIDER_CHAIN; skipped", name
            )
            continue
        if cls is ClassicProvider:
            continue
        chain.append(cls())
    chain.append(ClassicProvider())
    return chain
