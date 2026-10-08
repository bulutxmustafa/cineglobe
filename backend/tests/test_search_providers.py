"""Unit tests for LLM providers, the provider chain router and the cost guard.
No real API is called: SDK clients are faked, SDK exception classes are real."""

import json
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import anthropic
import httpx
import httpx2
import pytest
from apps.search import cost_guard
from apps.search.models import LLMUsageLog
from apps.search.prompts import PARSE_SYSTEM_PROMPT
from apps.search.providers import build_chain
from apps.search.providers.anthropic import PARSE_MAX_TOKENS as CLAUDE_PARSE_MAX
from apps.search.providers.anthropic import AnthropicProvider
from apps.search.providers.base import (
    ProviderError,
    ProviderOutputError,
    ProviderUnavailableError,
    TitleBrief,
)
from apps.search.providers.classic import ClassicProvider
from apps.search.providers.gemini import PARSE_MAX_TOKENS as GEMINI_PARSE_MAX
from apps.search.providers.gemini import GeminiProvider, response_schema
from apps.search.router import LLMRouter, Quota
from apps.search.schemas import ReasonList, SearchFilters
from django.core.cache import cache
from google.genai import errors as genai_errors
from search_fakes import FakeProvider

pytestmark = pytest.mark.django_db

_REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
BRIEF = TitleBrief("movie:1", "movie", "Heat", "1995", ["Crime"], 8.3, "Two men.")


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _status_error(cls, code):
    return cls("err", response=httpx2.Response(code, request=_REQUEST), body=None)


# ---------------------------------------------------------------------------
# AnthropicProvider
# ---------------------------------------------------------------------------


class FakeAnthropic:
    def __init__(self, result=None, error=None, stop_reason="end_turn"):
        self.result, self.error, self.stop_reason = result, error, stop_reason
        self.calls = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            parsed_output=self.result,
            usage=SimpleNamespace(input_tokens=900, output_tokens=200),
        )


def test_anthropic_parse_uses_haiku_structured_output(settings):
    settings.ANTHROPIC_MODEL_PARSER = "claude-haiku-5-5"
    client = FakeAnthropic(SearchFilters(genres_include=["Thriller"]))

    result = AnthropicProvider(client).parse_query("gerilim")

    call = client.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["system"] == PARSE_SYSTEM_PROMPT
    assert call["output_format"] is SearchFilters
    assert call["max_tokens"] == CLAUDE_PARSE_MAX
    assert call["messages"][0]["content"] == "<user_query>\ngerilim\n</user_query>"
    assert result.value.genres_include == ["Thriller"]
    assert (result.model, result.input_tokens, result.output_tokens) == (
        "claude-haiku-5-5",
        900,
        200,
    )


def test_anthropic_explain_returns_mapping():
    reasons = ReasonList.model_validate(
        {"reasons": [{"key": "movie:1", "reason": "Gergin."}]}
    )
    result = AnthropicProvider(FakeAnthropic(reasons)).explain([BRIEF], "suç", "tr")
    assert result.value == {"movie:1": "Gergin."}


@pytest.mark.parametrize(
    "error, expected",
    [
        (anthropic.APIConnectionError(request=_REQUEST), ProviderUnavailableError),
        (anthropic.APITimeoutError(request=_REQUEST), ProviderUnavailableError),
        (_status_error(anthropic.RateLimitError, 429), ProviderUnavailableError),
        (_status_error(anthropic.AuthenticationError, 401), ProviderUnavailableError),
        (_status_error(anthropic.InternalServerError, 500), ProviderUnavailableError),
        (_status_error(anthropic.BadRequestError, 400), ProviderError),
        (ValueError("bad json"), ProviderOutputError),
    ],
)
def test_anthropic_error_mapping(error, expected):
    with pytest.raises(expected):
        AnthropicProvider(FakeAnthropic(error=error)).parse_query("x")


@pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal"])
def test_anthropic_unusable_stop_reason_is_bad_output(stop_reason):
    provider = AnthropicProvider(
        FakeAnthropic(SearchFilters(), stop_reason=stop_reason)
    )
    with pytest.raises(ProviderOutputError):
        provider.parse_query("x")


def test_anthropic_configuration_follows_api_key(settings):
    settings.ANTHROPIC_API_KEY = ""
    assert AnthropicProvider().is_configured() is False
    settings.ANTHROPIC_API_KEY = "sk-test"
    provider = AnthropicProvider()
    assert provider.is_configured() is True
    assert isinstance(provider.client, anthropic.Anthropic)
    assert provider.client.max_retries == 0
    assert provider.is_paid is True


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------


def fake_gemini(text=None, error=None):
    client = MagicMock()
    if error:
        client.models.generate_content.side_effect = error
    else:
        client.models.generate_content.return_value = SimpleNamespace(
            text=text,
            usage_metadata=SimpleNamespace(
                prompt_token_count=800,
                candidates_token_count=150,
                thoughts_token_count=20,
            ),
        )
    return client


def test_gemini_parse_sends_json_schema_and_counts_thinking_tokens(settings):
    settings.GEMINI_MODEL = "gemini-3.5-flash-lite"
    client = fake_gemini(json.dumps({"media_type": "tv", "genres_include": ["Comedy"]}))

    result = GeminiProvider(client).parse_query("komik dizi")

    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-3.5-flash-lite"
    assert kwargs["contents"] == "<user_query>\nkomik dizi\n</user_query>"
    config = kwargs["config"]
    assert config.system_instruction == PARSE_SYSTEM_PROMPT
    assert config.response_mime_type == "application/json"
    assert config.max_output_tokens == GEMINI_PARSE_MAX
    assert result.value.media_type == "tv"
    assert (result.input_tokens, result.output_tokens) == (800, 170)


def test_gemini_explain_returns_mapping():
    text = json.dumps(
        {"reasons": [{"key": "movie:1", "reason": "Gergin bir suç filmi."}]}
    )
    result = GeminiProvider(fake_gemini(text)).explain([BRIEF], "suç", "tr")
    assert result.value == {"movie:1": "Gergin bir suç filmi."}


def test_gemini_schema_strips_titles_and_defaults():
    schema = json.dumps(response_schema(SearchFilters))
    assert '"title"' not in schema and '"default"' not in schema
    assert '"genres_include"' in schema


@pytest.mark.parametrize(
    "error, expected",
    [
        (
            genai_errors.ClientError(429, {"error": {"message": "quota"}}),
            ProviderUnavailableError,
        ),
        (
            genai_errors.ClientError(403, {"error": {"message": "key"}}),
            ProviderUnavailableError,
        ),
        (genai_errors.ClientError(400, {"error": {"message": "bad"}}), ProviderError),
        (
            genai_errors.ServerError(503, {"error": {"message": "down"}}),
            ProviderUnavailableError,
        ),
        (httpx.ReadTimeout("slow"), ProviderUnavailableError),
    ],
)
def test_gemini_error_mapping(error, expected):
    with pytest.raises(expected):
        GeminiProvider(fake_gemini(error=error)).parse_query("x")


@pytest.mark.parametrize(
    "text", ["", "not json", json.dumps({"genres_include": ["Nope"]})]
)
def test_gemini_invalid_output(text):
    with pytest.raises(ProviderOutputError):
        GeminiProvider(fake_gemini(text)).parse_query("x")


def test_gemini_free_tier_is_not_paid(settings):
    settings.GEMINI_FREE_TIER = True
    assert GeminiProvider().is_paid is False
    settings.GEMINI_FREE_TIER = False
    assert GeminiProvider().is_paid is True


def test_gemini_configuration_follows_api_key(settings):
    settings.GEMINI_API_KEY = ""
    assert GeminiProvider().is_configured() is False
    settings.GEMINI_API_KEY = "g-test"
    assert GeminiProvider().is_configured() is True


# ---------------------------------------------------------------------------
# Chain construction (scenario 16: provider switch is env-only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "names, expected",
    [
        (["gemini", "classic"], [GeminiProvider, ClassicProvider]),
        (["anthropic", "classic"], [AnthropicProvider, ClassicProvider]),
        (["gemini", "anthropic"], [GeminiProvider, AnthropicProvider, ClassicProvider]),
        (["classic", "bogus"], [ClassicProvider]),
    ],
)
def test_build_chain_from_setting(settings, names, expected):
    settings.LLM_PROVIDER_CHAIN = names
    assert [type(p) for p in build_chain()] == expected


# ---------------------------------------------------------------------------
# LLMRouter
# ---------------------------------------------------------------------------


def router(*providers):
    return LLMRouter([*providers, ClassicProvider()])


def test_router_uses_first_working_provider_and_logs_usage():
    first = FakeProvider("gemini", SearchFilters(genres_include=["Drama"]))
    outcome = router(first).parse("dram")

    assert (outcome.provider, outcome.ai_status, outcome.cacheable) == (
        "gemini",
        "ok",
        True,
    )
    assert outcome.filters.genres_include == ["Drama"]
    log = LLMUsageLog.objects.get()
    assert (log.provider, log.call_type, log.outcome) == ("gemini", "parse", "ok")
    assert (log.input_tokens, log.output_tokens) == (120, 40)


def test_router_without_configured_ai_uses_classic_and_is_cacheable():
    outcome = router(FakeProvider(configured=False)).parse("komedi")
    assert (outcome.provider, outcome.ai_status, outcome.cacheable) == (
        "classic",
        "fallback",
        True,
    )


def test_scenario_15_chain_falls_through_and_circuit_breaker_skips_provider():
    gemini = FakeProvider("gemini", parse_errors=[ProviderUnavailableError("429")])
    claude = FakeProvider("anthropic", SearchFilters(genres_include=["Crime"]))

    outcome = router(gemini, claude).parse("suç")
    assert outcome.provider == "anthropic"

    # Circuit for gemini is now open: the next request must not call it at all.
    router(gemini, claude).parse("suç 2")
    assert len(gemini.parse_calls) == 1
    assert len(claude.parse_calls) == 2


def test_scenario_15_everything_down_falls_back_to_classic():
    gemini = FakeProvider("gemini", parse_errors=[ProviderUnavailableError("timeout")])
    claude = FakeProvider("anthropic", parse_errors=[ProviderError("400")])

    outcome = router(gemini, claude).parse("gerilim, korku olmasın")

    assert (outcome.provider, outcome.ai_status, outcome.cacheable) == (
        "classic",
        "fallback",
        False,
    )
    assert outcome.filters.genres_exclude == ["Horror"]
    assert sorted(LLMUsageLog.objects.values_list("outcome", flat=True)) == [
        "error",
        "unavailable",
    ]


def test_circuit_closes_after_cooldown(settings):
    settings.LLM_CIRCUIT_BREAKER_SECONDS = 60
    gemini = FakeProvider("gemini", parse_errors=[ProviderUnavailableError("429")])
    router(gemini).parse("dram")
    assert cost_guard.circuit_open("gemini")
    cache.delete("llm:circuit_open:gemini")  # what the TTL does after 60 s
    assert router(gemini).parse("dram").ai_status == "ok"


def test_invalid_output_is_retried_once_on_same_provider():
    flaky = FakeProvider(
        "gemini",
        SearchFilters(genres_include=["Comedy"]),
        parse_errors=[ProviderOutputError("json")],
    )
    outcome = router(flaky).parse("komedi")
    assert outcome.provider == "gemini"
    assert len(flaky.parse_calls) == 2
    assert not cost_guard.circuit_open("gemini")  # bad output does not trip the breaker


def test_invalid_output_twice_moves_on():
    broken = FakeProvider(
        "gemini", parse_errors=[ProviderOutputError("a"), ProviderOutputError("b")]
    )
    assert router(broken).parse("komedi").provider == "classic"
    assert len(broken.parse_calls) == 2


def test_scenario_11_budget_exhausted_skips_paid_provider(settings):
    settings.LLM_DAILY_BUDGET_USD = 0.01
    cost_guard._add_spend(Decimal("0.02"))
    claude = FakeProvider("anthropic", paid=True)

    outcome = router(claude).parse("dram")

    assert (outcome.provider, outcome.ai_status) == ("classic", "budget_exceeded")
    assert claude.parse_calls == []


def test_budget_does_not_block_free_provider(settings):
    settings.LLM_DAILY_BUDGET_USD = 0.01
    cost_guard._add_spend(Decimal("0.02"))
    free = FakeProvider("gemini", paid=False)
    assert router(free).parse("dram").ai_status == "ok"


def test_scenario_12_quota_exhausted_uses_classic_without_calling_llm():
    llm = FakeProvider("gemini")
    quota = Quota("guest:abc", 1)

    assert router(llm).parse("dram", quota).ai_status == "ok"
    second = router(llm).parse("komedi", quota)

    assert (second.provider, second.ai_status, second.cacheable) == (
        "classic",
        "quota_exceeded",
        False,
    )
    assert len(llm.parse_calls) == 1


def test_quota_is_not_consumed_when_no_llm_would_run():
    quota = Quota("guest:abc", 1)
    router(FakeProvider(configured=False)).parse("dram", quota)
    assert cost_guard.quota_remaining("guest:abc", 1) == 1


def test_explain_ignores_invented_keys_and_falls_back_on_error():
    llm = FakeProvider("gemini", extra_reason_keys=["movie:999"])
    reasons = router(llm).explain([BRIEF], "suç", "en")
    assert reasons == {"movie:1": "[en] gemini reason for movie:1"}

    failing = FakeProvider("gemini", explain_error=ProviderOutputError("x"))
    assert router(failing).explain([BRIEF], "suç", "en") == {}
    assert len(failing.explain_calls) == 1  # no retry for explanations


def test_explain_with_no_titles_does_nothing():
    llm = FakeProvider("gemini")
    assert router(llm).explain([], "q", "tr") == {}
    assert llm.explain_calls == []


# ---------------------------------------------------------------------------
# Cost guard
# ---------------------------------------------------------------------------


def test_call_cost_for_paid_free_and_unknown_models():
    paid = FakeProvider("anthropic", paid=True)
    free = FakeProvider("gemini", paid=False)
    assert cost_guard.call_cost(paid, "claude-haiku-5-5", 2400, 700) == Decimal(
        "0.00059"
    )
    assert cost_guard.call_cost(free, "gemini-3.5-flash-lite", 2400, 700) == 0
    assert cost_guard.call_cost(paid, "unknown-model", 2400, 700) == 0


def test_scenario_13_usage_log_and_spend_counter_agree(settings):
    settings.LLM_DAILY_BUDGET_USD = 100
    claude = FakeProvider(
        "anthropic", paid=True, model="claude-haiku-5-5", tokens=(2400, 700)
    )
    r = router(claude)
    r.parse("dram")
    r.explain([BRIEF], "dram", "tr")

    logs = LLMUsageLog.objects.all()
    assert logs.count() == 2
    total = sum(log.cost_usd for log in logs)
    assert total == Decimal("0.00118")
    assert cost_guard.spent_today_usd() == total


def test_quota_identity_hashes_ip_and_prefers_user(settings):
    settings.GUEST_DAILY_AI_SEARCHES = 10
    settings.USER_DAILY_AI_SEARCHES = 40
    guest, guest_limit = cost_guard.quota_identity(None, "203.0.113.7")
    assert guest.startswith("guest:") and "203.0.113.7" not in guest
    assert guest_limit == 10
    assert cost_guard.quota_identity(5, "203.0.113.7") == ("user:5", 40)


def test_quota_resets_on_next_local_day():
    assert cost_guard.consume_quota("guest:x", 1) is True
    assert cost_guard.consume_quota("guest:x", 1) is False
    tomorrow = date.today() + timedelta(days=1)
    with patch("apps.search.cost_guard.local_today", return_value=tomorrow):
        assert cost_guard.consume_quota("guest:x", 1) is True


def test_local_day_uses_istanbul_time(settings):
    assert settings.QUOTA_TIME_ZONE == "Europe/Istanbul"
    assert 0 < cost_guard.seconds_until_local_midnight() <= 86400
