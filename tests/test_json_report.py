import json

from project_health.models import CheckResult, ProjectReport
from project_health.reports.json_report import JsonReport


def test_render_returns_json_with_project_report_data():
    report = ProjectReport(
        path="/tmp/project",
        score=85,
        status="ready",
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
            ),
            CheckResult(
                name="Dependencies",
                passed=True,
                score=100,
                metadata={
                    "requirements": {
                        "dependencies": {
                            "python": ["rich", "typer"],
                        },
                        "dev_dependencies": {
                            "python": ["pytest"],
                        },
                    },
                },
            ),
            CheckResult(
                name="Environment",
                passed=True,
                score=100,
                metadata={
                    "available_packages": ["rich", "typer"],
                    "available_dev_packages": [],
                },
            )
        ],
    )

    rendered = JsonReport().render(report)
    payload = json.loads(rendered)

    assert isinstance(rendered, str)
    assert payload["path"] == "/tmp/project"
    assert payload["score"] == 85
    assert payload["status"] == "ready"
    assert payload["checks"]
    assert payload["checks"][0]["name"] == "readme"
    assert payload["checks"][0]["passed"] is True
    assert payload["checks"][0]["score"] == 10
    assert payload["runtime_dependencies"] == ["rich", "typer"]
    assert payload["available_runtime_dependencies"] == ["rich", "typer"]
    assert payload["dev_dependencies"] == ["pytest"]
    assert payload["available_dev_dependencies"] == []
