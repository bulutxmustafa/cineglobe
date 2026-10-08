"""Shared Anthropic client factory for the search pipeline."""

from __future__ import annotations

import anthropic
from django.conf import settings


def get_llm_client() -> anthropic.Anthropic | None:
    """Return a configured Anthropic client, or None when no API key is set.

    Returning None lets callers go straight to their deterministic fallback
    instead of paying for a request that would fail with 401.
    """
    if not settings.ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )
