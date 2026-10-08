"""GeminiProvider: Google Gemini (default Flash-Lite, free tier) with JSON schema output.

Free-tier requests may be used by Google to improve its products, so callers
must only send the query text and public title metadata (plan §3.10).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pydantic
from django.conf import settings
from pydantic import BaseModel

from apps.search.prompts import (
    EXPLAIN_SYSTEM_PROMPT,
    PARSE_SYSTEM_PROMPT,
    explain_user_message,
    parse_user_message,
)
from apps.search.providers.base import (
    LLMProvider,
    LLMResult,
    ProviderError,
    ProviderOutputError,
    ProviderUnavailableError,
    TitleBrief,
)
from apps.search.schemas import ReasonList, SearchFilters

if TYPE_CHECKING:
    from google import genai

# The SDK is imported on first use, not at module import: `google.genai`
# takes ~0.8 s to import, and on serverless every cold start would pay for it even
# when this provider is not in LLM_PROVIDER_CHAIN (plan v1.8).

PARSE_MAX_TOKENS = 1024
EXPLAIN_MAX_TOKENS = 2048
# Status codes that mean "try again later" (or misconfiguration we should not hammer).
UNAVAILABLE_CODES = {401, 403, 408, 429}


def response_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic JSON schema without 'title'/'default' keys, which Gemini does not need."""

    def strip(node: Any) -> Any:
        if isinstance(node, dict):
            return {
                k: strip(v)
                for k, v in node.items()
                if k not in {"title", "default"} or isinstance(v, dict)
            }
        if isinstance(node, list):
            return [strip(v) for v in node]
        return node

    return strip(model.model_json_schema())


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, client: genai.Client | None = None) -> None:
        self._client = client

    @property
    def is_paid(self) -> bool:  # type: ignore[override]
        return not settings.GEMINI_FREE_TIER

    def is_configured(self) -> bool:
        return self._client is not None or bool(settings.GEMINI_API_KEY)

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(
                    timeout=int(settings.LLM_TIMEOUT_SECONDS * 1000)
                ),
            )
        return self._client

    def parse_query(self, query: str) -> LLMResult[SearchFilters]:
        return self._call(
            system=PARSE_SYSTEM_PROMPT,
            content=parse_user_message(query),
            output_model=SearchFilters,
            max_tokens=PARSE_MAX_TOKENS,
        )

    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> LLMResult[dict[str, str]]:
        titles_json = json.dumps([t.as_dict() for t in titles], ensure_ascii=False)
        result = self._call(
            system=EXPLAIN_SYSTEM_PROMPT,
            content=explain_user_message(titles_json, query, language),
            output_model=ReasonList,
            max_tokens=EXPLAIN_MAX_TOKENS,
        )
        return LLMResult(
            result.value.as_mapping(),
            result.model,
            result.input_tokens,
            result.output_tokens,
        )

    def _call(
        self,
        *,
        system: str,
        content: str,
        output_model: type[BaseModel],
        max_tokens: int,
    ) -> LLMResult:
        from google.genai import errors, types

        model = settings.GEMINI_MODEL
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=response_schema(output_model),
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.MINIMAL
            ),
        )
        try:
            response = self.client.models.generate_content(
                model=model, contents=content, config=config
            )
        except errors.ServerError as exc:
            raise ProviderUnavailableError(f"gemini: {exc}") from exc
        except errors.ClientError as exc:
            if exc.code in UNAVAILABLE_CODES:
                raise ProviderUnavailableError(f"gemini: {exc}") from exc
            raise ProviderError(f"gemini: {exc}") from exc
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise ProviderUnavailableError(f"gemini: {exc}") from exc

        text = response.text
        if not text:
            raise ProviderOutputError("gemini: empty response")
        try:
            value = output_model.model_validate_json(text)
        except pydantic.ValidationError as exc:
            raise ProviderOutputError(f"gemini: invalid output: {exc}") from exc

        usage = response.usage_metadata
        input_tokens = (usage.prompt_token_count or 0) if usage else 0
        # Thinking tokens are billed as output on paid tiers.
        output_tokens = (
            (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
            if usage
            else 0
        )
        return LLMResult(value, model, input_tokens, output_tokens)
