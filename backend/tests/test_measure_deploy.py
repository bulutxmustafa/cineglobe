"""Tests for the hosting spike measurement command."""

from io import StringIO

import httpx
from apps.catalog.management.commands import measure_deploy
from apps.catalog.management.commands.measure_deploy import Command, p95

TABLE = """# Spike
| Tarih | İlk istek | Sıcak ort. | Sıcak p95 | Hata | Karar |
|---|---|---|---|---|---|
| — | — | — | — | — | bekleniyor |
"""


def run(tmp_path, handler, warm=5):
    report = tmp_path / "spike.md"
    report.write_text(TABLE, encoding="utf-8")
    command = Command(stdout=StringIO())
    command.http_client = httpx.Client(transport=httpx.MockTransport(handler))
    command.handle(
        base_url="https://x.vercel.app/", warm=warm, report=str(report), no_report=False
    )
    return command.stdout.getvalue(), report.read_text(encoding="utf-8")


def test_records_passing_measurement(tmp_path):
    seen = []

    def ok(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"status": "ok"})

    out, report = run(tmp_path, ok)
    assert "passed=True" in out
    assert seen[0] == "https://x.vercel.app/api/v1/health/" and len(seen) == 6
    assert "bekleniyor" not in report and "✅" in report


def test_errors_fail_the_gate(tmp_path):
    out, report = run(tmp_path, lambda r: httpx.Response(503))
    assert "errors=6" in out and "passed=False" in out
    assert "❌" in report


def test_second_run_appends_a_new_row(tmp_path):
    report = tmp_path / "spike.md"
    report.write_text(TABLE, encoding="utf-8")
    for _ in range(2):
        command = Command(stdout=StringIO())
        command.http_client = httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200))
        )
        command.handle(
            base_url="https://x.vercel.app", warm=1, report=str(report), no_report=False
        )
    rows = [
        line for line in report.read_text(encoding="utf-8").splitlines() if "✅" in line
    ]
    assert len(rows) == 2


def test_p95():
    assert p95([float(i) for i in range(1, 101)]) == 95.0
    assert p95([3.0]) == 3.0


def test_report_path_points_to_repo_docs():
    assert measure_deploy.REPORT.as_posix().endswith("docs/deploy-spike.md")
    assert measure_deploy.REPORT.exists()
