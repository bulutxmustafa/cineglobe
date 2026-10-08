"""AnthropicProvider: Claude (default Haiku 5.5) via structured outputs."""

from __future__ import annotations

import json

import anthropic
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

PARSE_MAX_TOKENS = 2048
EXPLAIN_MAX_TOKENS = 4096


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    is_paid = True

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self._client = client

    def is_configured(self) -> bool:
        return self._client is not None or bool(settings.ANTHROPIC_API_KEY)

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=0,  # the chain decides what happens after a failure
            )
        return self._client

    def parse_query(self, query: str) -> LLMResult[SearchFilters]:
        return self._call(
            model=settings.ANTHROPIC_MODEL_PARSER,
            system=PARSE_SYSTEM_PROMPT,
            content=parse_user_message(query),
            output_format=SearchFilters,
            max_tokens=PARSE_MAX_TOKENS,
        )

    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> LLMResult[dict[str, str]]:
        titles_json = json.dumps([t.as_dict() for t in titles], ensure_ascii=False)
        result = self._call(
            model=settings.ANTHROPIC_MODEL_EXPLAIN,
            system=EXPLAIN_SYSTEM_PROMPT,
            content=explain_user_message(titles_json, query, language),
            output_format=ReasonList,
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
        model: str,
        system: str,
        content: str,
        output_format: type[BaseModel],
        max_tokens: int,
    ) -> LLMResult:
        try:
            response = self.client.messages.parse(
                model=model,
                max_tokens=max_tokens,
                system=system,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": content}],
                output_format=output_format,
            )
        except (
            anthropic.APIConnectionError,  # includes APITimeoutError
            anthropic.RateLimitError,
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
        ) as exc:
            raise ProviderUnavailableError(f"anthropic: {exc}") from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500:
                raise ProviderUnavailableError(f"anthropic: {exc}") from exc
            raise ProviderError(f"anthropic: {exc}") from exc
        except (pydantic.ValidationError, ValueError) as exc:
            raise ProviderOutputError(f"anthropic: invalid output: {exc}") from exc

        if response.stop_reason != "end_turn" or response.parsed_output is None:
            raise ProviderOutputError(
                f"anthropic: unusable response (stop_reason={response.stop_reason})"
            )
        usage = response.usage
        return LLMResult(
            response.parsed_output,
            model,
            usage.input_tokens or 0,
            usage.output_tokens or 0,
        )
