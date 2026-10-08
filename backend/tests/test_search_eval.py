"""Tests for the LLM quality gate (evaluation module and run_llm_eval command)."""

from io import StringIO

import pytest
from apps.search.evaluation import (
    EvalReport,
    check_expectations,
    load_queries,
    run_eval,
)
from apps.search.providers.base import ProviderOutputError, ProviderUnavailableError
from apps.search.providers.classic import ClassicProvider
from apps.search.schemas import SearchFilters
from django.core.management import CommandError, call_command
from search_fakes import FakeProvider


def test_eval_set_has_mandatory_and_real_queries():
    queries = load_queries()
    ids = [q["id"] for q in queries]
    assert len(ids) == len(set(ids)) >= 29  # 9 mandatory + at least 20 real
    assert sum(1 for q in queries if q["expect"].get("injection")) >= 2
    assert sum(1 for q in queries if q["expect"].get("genres_exclude_all")) >= 3


def test_check_expectations_reports_each_failure():
    filters = SearchFilters(
        media_type="tv", genres_include=["Horror"], keywords=["spy"]
    )
    failures = check_expectations(
        filters,
        {
            "media_type": "movie",
            "genres_exclude_all": ["Horror"],
            "keywords_any": ["spy"],
            "year_from_lte": 1990,
        },
    )
    assert len(failures) == 3
    assert any(f.startswith("exclude violation: Horror") for f in failures)


def test_check_expectations_meaningless():
    assert (
        check_expectations(SearchFilters(is_meaningful=False), {"meaningful": False})
        == []
    )
    assert check_expectations(SearchFilters(), {"meaningful": False})


QUERIES = [
    {"id": "a", "query": "x", "expect": {"media_type": "tv"}},
    {"id": "b", "query": "y", "expect": {"genres_exclude_all": ["Horror"]}},
    {"id": "c", "query": "z", "expect": {"injection": True, "meaningful": False}},
]


def test_run_eval_scores_gate_passing_provider():
    good = FakeProvider(
        "gemini", SearchFilters(media_type="tv", genres_exclude=["Horror"])
    )
    good_c = run_eval(good, QUERIES[:2], "m")
    assert good_c.passed
    assert good_c.valid_rate == good_c.first_try_rate == 1.0


def test_run_eval_gate_failures():
    # Errors are consumed in order by query "a": bad JSON, then 429 on the retry.
    flaky = FakeProvider(
        "gemini",
        SearchFilters(media_type="movie"),
        parse_errors=[ProviderOutputError("json"), ProviderUnavailableError("429")],
    )
    report = run_eval(flaky, QUERIES, "m")
    # a: no usable output; b: Horror not excluded; c: injection not refused
    assert report.first_try_rate == pytest.approx(2 / 3)
    assert report.valid_rate == pytest.approx(2 / 3)
    assert report.media_type_rate == 0
    assert report.exclude_violations == 1
    assert report.injection_ok is False
    assert not report.passed
    md = report.to_markdown("2026-10-08")
    assert "KALDI" in md and "`a`" in md and "provider error" in md


def test_run_eval_counts_retry_success_as_valid_but_not_first_try():
    flaky = FakeProvider(
        "gemini",
        SearchFilters(media_type="tv"),
        parse_errors=[ProviderOutputError("json")],
    )
    case = run_eval(flaky, QUERIES[:1], "m").cases[0]
    assert (case.valid, case.valid_first_try, case.passed) == (True, False, True)
    assert len(flaky.parse_calls) == 2


def test_empty_report_is_neutral():
    report = EvalReport("gemini", "m", [])
    assert report.avg_seconds == 0 and report.valid_rate == 1.0


def test_command_requires_configured_provider(settings):
    settings.GEMINI_API_KEY = ""
    with pytest.raises(CommandError):
        call_command("run_llm_eval", "--provider", "gemini")


def test_command_runs_classic_and_appends_report(tmp_path):
    report = tmp_path / "llm-eval.md"
    report.write_text("# LLM eval\n", encoding="utf-8")
    out = StringIO()

    call_command(
        "run_llm_eval", "--provider", "classic", "--report", str(report), stdout=out
    )

    text = report.read_text(encoding="utf-8")
    assert text.startswith("# LLM eval\n\n## ")
    assert "`classic` (`rules`)" in text
    assert "Report appended" in out.getvalue()


def test_command_warns_when_gate_fails(tmp_path, monkeypatch):
    queries = tmp_path / "q.json"
    queries.write_text(
        '[{"id": "x", "query": "komedi", "expect": {"media_type": "tv"}}]',
        encoding="utf-8",
    )
    out = StringIO()
    call_command(
        "run_llm_eval", "--provider", "classic", "--queries", str(queries), stdout=out
    )
    assert "Quality gate FAILED" in out.getvalue()


def test_classic_provider_passes_gate_on_shipped_set():
    assert run_eval(ClassicProvider(), load_queries(), "rules").passed


def test_run_eval_paces_requests_to_stay_under_rate_limit():
    waits = []
    llm = FakeProvider(
        "gemini",
        SearchFilters(media_type="tv"),
        parse_errors=[ProviderOutputError("json")],
    )
    run_eval(llm, QUERIES[:2], "m", requests_per_minute=12, sleep=waits.append)
    # 3 calls (one retry) → 2 waits of up to 5 s each (60 / 12)
    assert len(waits) == 2
    assert all(0 < w <= 5.0 for w in waits)


def test_long_errors_are_truncated_in_report():
    broken = FakeProvider("gemini", parse_errors=[ProviderUnavailableError("x" * 1000)])
    md = run_eval(broken, QUERIES[:1], "m").to_markdown("2026-10-08")
    assert "x" * 300 not in md and "x" * 150 in md


def test_latency_excludes_pacing_waits():
    def slow_sleep(seconds):  # a real sleep would be counted if timing were wrong
        import time

        time.sleep(0.05)

    llm = FakeProvider("gemini", SearchFilters(media_type="tv"))
    report = run_eval(
        llm, QUERIES[:1] * 3, "m", requests_per_minute=6000, sleep=slow_sleep
    )
    assert report.avg_seconds < 0.02
