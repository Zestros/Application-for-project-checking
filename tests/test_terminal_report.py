from rich.console import Console

from project_health.models import CheckResult, CommandResult, ProjectReport
from project_health.reports.terminal_report import TerminalReport


def test_render_prints_project_report_data():
    report = ProjectReport(
        path="/tmp/project",
        score=85,
        status="Good",
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
                issues=["missing badges"],
                recommendations=["add badges"],
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
        recommendations=["improve docs"],
        detected_stack=["Python"],
        required_tools=["Docker"],
        available_tools={
            "git": CommandResult(
                command=["git", "--version"],
                available=True,
                output="git version 2.0.0",
                error=None,
            )
        },
    )
    console = Console(record=True)
    report_renderer = TerminalReport(console=console)

    report_renderer.render(report)
    output = console.export_text()

    assert "/tmp/project" in output
    assert "85" in output
    assert "Good" in output
    assert "readme" in output
    assert "missing badges" in output
    assert "Python" in output
    assert "Docker" in output
    assert "git" in output
    assert "Project Health Analyzer" in output
    assert "Required:" in output
    assert "Available:" in output
    assert "Runtime deps" in output
    assert "rich, typer" in output
    assert "Available runtime deps" in output
    assert "Dev deps" in output
    assert "pytest" in output
    assert "Status" in output
    assert "Recommendations" in output


def test_join_returns_items_joined_by_comma():
    report_renderer = TerminalReport(console=Console(record=True))

    assert report_renderer._join(["Python", "Docker"]) == "Python, Docker"


def test_join_returns_none_detected_for_empty_list():
    report_renderer = TerminalReport(console=Console(record=True))

    assert report_renderer._join([]) == "None detected"


def test_status_color_returns_expected_values():
    report_renderer = TerminalReport(console=Console(record=True))

    assert report_renderer._status_color("Critical") == "bold red"
    assert report_renderer._status_color("Weak") == "bold yellow"
    assert report_renderer._status_color("Good") == "bold green"
    assert report_renderer._status_color("Excellent") == "bold bright_green"
    assert report_renderer._status_color("Unknown") == "white"
