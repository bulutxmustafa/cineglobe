"""LLM quality gate (plan §3.10): run the eval set against one provider and score it.

Gate (all must hold to keep the provider):
1. valid JSON ≥ 95 % (after one retry) and ≥ 90 % on the first try
2. media_type correct ≥ 90 % (of queries that state an expected media_type)
3. zero genres_exclude violations
4. every prompt-injection query passes
5. average latency within LLM_EVAL_MAX_AVG_SECONDS
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apps.search.providers.base import LLMProvider, ProviderError, ProviderOutputError
from apps.search.schemas import SearchFilters

QUERIES_PATH = Path(__file__).parent / "eval" / "queries.json"
MAX_AVG_SECONDS = 6.0


def load_queries(path: Path = QUERIES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_expectations(filters: SearchFilters, expect: dict[str, Any]) -> list[str]:
    """Return human-readable failures (empty list = case passed)."""
    failures: list[str] = []
    meaningful = expect.get("meaningful", True)
    if filters.is_meaningful != meaningful:
        failures.append(f"is_meaningful={filters.is_meaningful}, expected {meaningful}")
        return failures
    if not meaningful:
        return failures

    def need(cond: bool, message: str) -> None:
        if not cond:
            failures.append(message)

    if "media_type" in expect:
        need(
            filters.media_type == expect["media_type"],
            f"media_type={filters.media_type}, expected {expect['media_type']}",
        )
    if wanted := expect.get("genres_include_any"):
        need(
            bool(set(wanted) & set(filters.genres_include)),
            f"genres_include={filters.genres_include}, expected any of {wanted}",
        )
    for genre in expect.get("genres_exclude_all", []):
        need(
            genre in filters.genres_exclude and genre not in filters.genres_include,
            f"exclude violation: {genre} (include={filters.genres_include}, "
            f"exclude={filters.genres_exclude})",
        )
    if wanted := expect.get("keywords_any"):
        need(
            bool({k.lower() for k in wanted} & set(filters.keywords)),
            f"keywords={filters.keywords}, expected any of {wanted}",
        )
    if wanted := expect.get("people_any"):
        need(
            bool({p.lower() for p in wanted} & set(filters.people)),
            f"people={filters.people}, expected any of {wanted}",
        )
    for key, field_name, op in (
        ("episode_runtime_max_lte", "episode_runtime_max", "lte"),
        ("max_seasons_lte", "max_seasons", "lte"),
        ("year_from_lte", "year_from", "lte"),
        ("year_to_gte", "year_to", "gte"),
    ):
        if key in expect:
            value = getattr(filters, field_name)
            ok = value is not None and (
                value <= expect[key] if op == "lte" else value >= expect[key]
            )
            need(ok, f"{field_name}={value}, expected {op} {expect[key]}")
    if "status" in expect:
        need(
            filters.status == expect["status"],
            f"status={filters.status}, expected {expect['status']}",
        )
    return failures


@dataclass
class CaseResult:
    id: str
    query: str
    seconds: float
    valid_first_try: bool
    valid: bool
    failures: list[str] = field(default_factory=list)
    error: str = ""
    expect: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.valid and not self.failures


@dataclass
class EvalReport:
    provider: str
    model: str
    cases: list[CaseResult]
    max_avg_seconds: float = MAX_AVG_SECONDS

    def _rate(self, numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 1.0

    @property
    def valid_rate(self) -> float:
        return self._rate(sum(c.valid for c in self.cases), len(self.cases))

    @property
    def first_try_rate(self) -> float:
        return self._rate(sum(c.valid_first_try for c in self.cases), len(self.cases))

    @property
    def media_type_rate(self) -> float:
        cases = [c for c in self.cases if "media_type" in c.expect]
        ok = sum(
            c.valid and not any(f.startswith("media_type=") for f in c.failures)
            for c in cases
        )
        return self._rate(ok, len(cases))

    @property
    def exclude_violations(self) -> int:
        # An exclusion case with no usable output counts as a violation: we
        # cannot show the excluded genre was kept out.
        return sum(
            1
            for c in self.cases
            if (not c.valid and c.expect.get("genres_exclude_all"))
            or any(f.startswith("exclude violation") for f in c.failures)
        )

    @property
    def injection_ok(self) -> bool:
        return all(c.passed for c in self.cases if c.expect.get("injection"))

    @property
    def avg_seconds(self) -> float:
        return (
            sum(c.seconds for c in self.cases) / len(self.cases) if self.cases else 0.0
        )

    @property
    def gate(self) -> dict[str, bool]:
        return {
            "valid JSON ≥ 95% (≥ 90% first try)": self.valid_rate >= 0.95
            and self.first_try_rate >= 0.90,
            "media_type ≥ 90%": self.media_type_rate >= 0.90,
            "genres_exclude violations = 0": self.exclude_violations == 0,
            "prompt injection passes": self.injection_ok,
            f"avg latency ≤ {self.max_avg_seconds:g}s": self.avg_seconds
            <= self.max_avg_seconds,
        }

    @property
    def passed(self) -> bool:
        return all(self.gate.values())

    def to_markdown(self, run_date: str) -> str:
        lines = [
            f"## {run_date} — `{self.provider}` (`{self.model}`)",
            "",
            f"**Sonuç: {'✅ GEÇTİ' if self.passed else '❌ KALDI'}** — "
            f"{sum(c.passed for c in self.cases)}/{len(self.cases)} sorgu tamamen doğru",
            "",
            "| Kriter | Değer | Durum |",
            "|---|---|---|",
            f"| Geçerli JSON (yeniden denemeyle / ilk denemede) | {self.valid_rate:.0%} / {self.first_try_rate:.0%} | {'✅' if self.gate['valid JSON ≥ 95% (≥ 90% first try)'] else '❌'} |",
            f"| `media_type` doğruluğu | {self.media_type_rate:.0%} | {'✅' if self.gate['media_type ≥ 90%'] else '❌'} |",
            f"| `genres_exclude` ihlali | {self.exclude_violations} | {'✅' if self.exclude_violations == 0 else '❌'} |",
            f"| Prompt injection | {'geçti' if self.injection_ok else 'kaldı'} | {'✅' if self.injection_ok else '❌'} |",
            f"| Ortalama süre | {self.avg_seconds:.2f} sn | {'✅' if self.avg_seconds <= self.max_avg_seconds else '❌'} |",
            "",
        ]
        failed = [c for c in self.cases if not c.passed]
        if failed:
            lines += ["<details><summary>Başarısız sorgular</summary>", ""]
            for c in failed:
                reason = c.error or "; ".join(c.failures)
                lines.append(f"- `{c.id}` “{c.query}” → {reason}")
            lines += ["", "</details>", ""]
        return "\n".join(lines)


def run_eval(
    provider: LLMProvider, queries: list[dict[str, Any]], model: str
) -> EvalReport:
    cases: list[CaseResult] = []
    for item in queries:
        started = time.monotonic()
        filters: SearchFilters | None = None
        first_try = True
        error = ""
        for _ in range(2):  # one retry after invalid output, as in production
            try:
                filters = provider.parse_query(item["query"]).value
                break
            except ProviderOutputError as exc:
                first_try = False
                error = f"invalid output: {exc}"
            except ProviderError as exc:
                first_try = False
                error = f"provider error: {exc}"
                break
        seconds = time.monotonic() - started
        expect = item.get("expect", {})
        if filters is None:
            cases.append(
                CaseResult(
                    item["id"], item["query"], seconds, False, False, [], error, expect
                )
            )
            continue
        cases.append(
            CaseResult(
                item["id"],
                item["query"],
                seconds,
                first_try,
                True,
                check_expectations(filters, expect),
                "",
                expect,
            )
        )
    return EvalReport(provider.name, model, cases)
