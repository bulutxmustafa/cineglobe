"""Measure cold and warm latency of a deployed API (plan v1.8 hosting spike).

    python backend/manage.py measure_deploy https://cineglobe.vercel.app

Run it after the deployment has been idle for 10+ minutes, so the first request
includes the Vercel cold start and the Neon wake-up. The result is appended to
docs/deploy-spike.md with the decision-gate verdict.
"""

from __future__ import annotations

import statistics
import time
from datetime import date
from pathlib import Path

import httpx
from django.core.management.base import BaseCommand, CommandError

HEALTH_PATH = "/api/v1/health/"
COLD_LIMIT_S = 5.0
WARM_LIMIT_MS = 800.0
REPORT = Path(__file__).resolve().parents[5] / "docs" / "deploy-spike.md"


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(int(round(0.95 * len(ordered))) - 1, 0)]


class Command(BaseCommand):
    help = "Measure cold/warm latency of a deployment and record it in docs/deploy-spike.md."

    def add_arguments(self, parser):
        parser.add_argument("base_url")
        parser.add_argument(
            "--warm", type=int, default=20, help="Number of warm requests"
        )
        parser.add_argument("--report", default=str(REPORT))
        parser.add_argument("--no-report", action="store_true")

    def handle(
        self, *args, base_url: str, warm: int, report: str, no_report: bool, **_
    ):
        url = base_url.rstrip("/") + HEALTH_PATH
        client = getattr(self, "http_client", None) or httpx.Client(timeout=60.0)
        errors = 0

        def timed_get() -> float:
            nonlocal errors
            started = time.monotonic()
            try:
                response = client.get(url)
                if response.status_code != 200:
                    errors += 1
            except httpx.HTTPError:
                errors += 1
            return time.monotonic() - started

        cold = timed_get()
        warm_ms = [timed_get() * 1000 for _ in range(warm)]
        if not warm_ms:
            raise CommandError("--warm must be at least 1")

        avg, high = statistics.mean(warm_ms), p95(warm_ms)
        passed = cold <= COLD_LIMIT_S and avg <= WARM_LIMIT_MS and errors == 0
        verdict = (
            "✅ Vercel + Neon ile devam"
            if passed
            else "❌ kullanıcıya rapor, yedek plan"
        )
        row = (
            f"| {date.today().isoformat()} | {cold:.2f} sn | {avg:.0f} ms | {high:.0f} ms "
            f"| {errors} | {verdict} |"
        )
        self.stdout.write(
            f"cold={cold:.2f}s warm_avg={avg:.0f}ms warm_p95={high:.0f}ms errors={errors} "
            f"passed={passed}"
        )

        if not no_report:
            path = Path(report)
            text = path.read_text(encoding="utf-8")
            placeholder = "| — | — | — | — | — | bekleniyor |"
            if placeholder in text:
                text = text.replace(placeholder, row)
            else:
                marker = "| Tarih | İlk istek |"
                head, _, tail = text.partition(marker)
                header_line, _, rest = tail.partition("\n")
                separator, _, rest = rest.partition("\n")
                text = f"{head}{marker}{header_line}\n{separator}\n{row}\n{rest}"
            path.write_text(text, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Recorded in {path}"))
