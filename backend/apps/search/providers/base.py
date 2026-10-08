"""LLMProvider interface shared by every search AI backend (plan §3.10).

Business logic only talks to this interface; which concrete provider runs is
decided by LLM_PROVIDER_CHAIN in the environment, never in code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from apps.search.schemas import SearchFilters

T = TypeVar("T")


class ProviderError(Exception):
    """Base class for provider failures; the chain moves to the next provider."""


class ProviderUnavailableError(ProviderError):
    """Transient failure (429, timeout, 5xx, network). Opens the circuit breaker."""


class ProviderOutputError(ProviderError):
    """The provider answered but the output was unusable (invalid JSON, refusal, truncation)."""


@dataclass(frozen=True)
class LLMResult(Generic[T]):
    value: T
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class TitleBrief:
    """The only title data an LLM ever sees: public catalogue metadata, nothing personal."""

    key: str
    media_type: str
    title: str
    year: str
    genres: list[str]
    rating: float | None
    overview: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "media_type": self.media_type,
            "title": self.title,
            "year": self.year,
            "genres": self.genres,
            "rating": self.rating,
            "overview": self.overview,
        }


class LLMProvider(ABC):
    #: Name used in LLM_PROVIDER_CHAIN and in usage logs.
    name: str
    #: False for the rule-based provider: no API calls, no cost, no quota.
    uses_ai: bool = True
    #: True when calls cost money (budget cap applies).
    is_paid: bool = False

    def is_configured(self) -> bool:
        """False when the provider lacks credentials; the chain skips it silently."""
        return True

    @abstractmethod
    def parse_query(self, query: str) -> LLMResult[SearchFilters]:
        """Turn a free-text request into validated SearchFilters."""

    @abstractmethod
    def explain(
        self, titles: list[TitleBrief], query: str, language: str
    ) -> LLMResult[dict[str, str]]:
        """Return {title key: one-sentence reason} for the given titles."""
