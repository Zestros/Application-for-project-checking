import importlib
import json
from dataclasses import asdict
from pathlib import Path

from typer.testing import CliRunner

from project_health import __version__
from project_health.models import CheckResult, ProjectReport, ScanFacts

cli = importlib.import_module("project_health.cli")
app = cli.app

runner = CliRunner()


def make_scan_facts(path):
    return ScanFacts(
        path=str(path),
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
            )
        ],
    )


def make_project_report(path):
    return ProjectReport(
        path=str(path),
        score=85,
        status="ready",
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
            )
        ],
    )


def test_version_prints_package_version():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "project-health" in result.stdout
    assert __version__ in result.stdout


def test_scan_json_output_uses_fake_dependencies(monkeypatch, tmp_path):
    scan_facts = make_scan_facts(tmp_path)
    project_report = make_project_report(tmp_path)
    seen = {}

    class FakeProjectScanner:
        def __init__(self, path):
            seen["scanner_path"] = path
            self.path = path

        def scan(self):
            return scan_facts

    class FakeReadinessAnalyzer:
        def analyze(self, facts):
            assert facts == scan_facts
            return project_report

    class FakeJsonReport:
        def render(self, report):
            assert report == project_report
            return json.dumps(asdict(report))

    def fake_load_renderer(output_format):
        seen["output_format"] = output_format
        return FakeJsonReport

    monkeypatch.setattr(cli, "_load_scanner", lambda: FakeProjectScanner)
    monkeypatch.setattr(cli, "_load_analyzer", lambda: FakeReadinessAnalyzer)
    monkeypatch.setattr(cli, "_load_renderer", fake_load_renderer)

    result = runner.invoke(app, ["scan", str(tmp_path), "--output-format", "json"])

    assert result.exit_code == 0
    assert seen["scanner_path"] == Path(tmp_path)
    assert seen["output_format"] == "json"
    payload = json.loads(result.stdout)
    assert payload["score"] == project_report.score
    assert payload["status"] == project_report.status
    assert payload["path"] == str(tmp_path)
    assert "checks" in payload


def test_scan_terminal_output_uses_fake_dependencies(monkeypatch, tmp_path):
    scan_facts = make_scan_facts(tmp_path)
    project_report = make_project_report(tmp_path)
    seen = {}

    class FakeProjectScanner:
        def __init__(self, path):
            seen["scanner_path"] = path
            self.path = path

        def scan(self):
            return scan_facts

    class FakeReadinessAnalyzer:
        def analyze(self, facts):
            assert facts == scan_facts
            return project_report

    class FakeTerminalReport:
        def render(self, report):
            assert report == project_report
            return "terminal report output"

    def fake_load_renderer(output_format):
        seen["output_format"] = output_format
        return FakeTerminalReport

    monkeypatch.setattr(cli, "_load_scanner", lambda: FakeProjectScanner)
    monkeypatch.setattr(cli, "_load_analyzer", lambda: FakeReadinessAnalyzer)
    monkeypatch.setattr(cli, "_load_renderer", fake_load_renderer)

    result = runner.invoke(app, ["scan", str(tmp_path), "--output-format", "terminal"])

    assert result.exit_code == 0
    assert seen["scanner_path"] == Path(tmp_path)
    assert seen["output_format"] == "terminal"
    assert "terminal report output" in result.stdout


def test_scan_with_missing_path_returns_error():
    missing_path = "/tmp/project-health-path-that-does-not-exist"

    result = runner.invoke(app, ["scan", missing_path, "--output-format", "json"])

    assert result.exit_code != 0
    assert "Path does not exist" in result.output
