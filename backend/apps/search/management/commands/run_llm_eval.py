"""Run the LLM quality gate against a live provider (plan §3.10).

Needs a real API key and costs real requests (free on the Gemini free tier),
so it is run by hand, never in CI:

    python backend/manage.py run_llm_eval --provider gemini --report docs/llm-eval.md
"""

from __future__ import annotations

import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.search.cost_guard import local_today
from apps.search.evaluation import QUERIES_PATH, load_queries, run_eval
from apps.search.providers import PROVIDERS

MODEL_SETTING = {
    "gemini": "GEMINI_MODEL",
    "anthropic": "ANTHROPIC_MODEL_PARSER",
    "classic": None,
}


def _console_safe(text: str) -> str:
    """Windows consoles (e.g. cp1254) cannot print ✅/❌; the report file stays UTF-8."""
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding)


class Command(BaseCommand):
    help = (
        "Score an LLM provider on the search eval set and optionally append a report."
    )

    def add_arguments(self, parser):
        parser.add_argument("--provider", choices=sorted(PROVIDERS), default="gemini")
        parser.add_argument("--queries", default=str(QUERIES_PATH))
        parser.add_argument(
            "--rpm",
            type=float,
            default=12,
            help="Max requests per minute (Gemini free tier allows 15; 0 = no pacing)",
        )
        parser.add_argument(
            "--report",
            help="Markdown file to append the dated result to (e.g. docs/llm-eval.md)",
        )

    def handle(self, *args, **options):
        provider = PROVIDERS[options["provider"]]()
        if not provider.is_configured():
            raise CommandError(
                f"Provider '{provider.name}' has no API key configured in .env."
            )
        setting = MODEL_SETTING.get(provider.name)
        model = getattr(settings, setting) if setting else "rules"

        queries = load_queries(Path(options["queries"]))
        # Classic makes no API calls, so it is never paced.
        rpm = options["rpm"] if provider.uses_ai else 0
        report = run_eval(provider, queries, model, requests_per_minute=rpm or None)
        markdown = report.to_markdown(local_today().isoformat())
        self.stdout.write(_console_safe(markdown))

        if options["report"]:
            path = Path(options["report"])
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            path.write_text(
                existing.rstrip() + "\n\n" + markdown.rstrip() + "\n", encoding="utf-8"
            )
            self.stdout.write(self.style.SUCCESS(f"Report appended to {path}"))

        if not report.passed:
            self.stdout.write(
                self.style.WARNING(
                    "Quality gate FAILED. Consider LLM_PROVIDER_CHAIN=anthropic,classic "
                    "(Claude Haiku 5.5) and re-run this command."
                )
            )
