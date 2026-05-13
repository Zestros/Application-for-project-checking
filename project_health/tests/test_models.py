from project_health.models import CheckResult, CommandResult, ProjectReport, ScanFacts


def test_command_result_stores_all_fields():
    result = CommandResult(
        command=["git", "--version"],
        available=True,
        output="git version 2.0.0",
        error=None,
    )

    assert result.command == ["git", "--version"]
    assert result.available is True
    assert result.output == "git version 2.0.0"
    assert result.error is None


def test_check_result_uses_independent_default_factories():
    first = CheckResult(name="readme", passed=True, score=10)
    second = CheckResult(name="license", passed=False, score=0)

    assert first.issues == []
    assert first.recommendations == []
    assert first.metadata == {}

    first.issues.append("missing badges")
    first.recommendations.append("add badges")
    first.metadata["source"] = "test"

    assert second.issues == []
    assert second.recommendations == []
    assert second.metadata == {}


def test_scan_facts_stores_data_and_defaults():
    check = CheckResult(name="readme", passed=True, score=10)
    facts = ScanFacts(path="/tmp/project", checks=[check])

    assert facts.path == "/tmp/project"
    assert facts.checks == [check]
    assert facts.detected_stack == []
    assert facts.required_tools == []
    assert facts.available_tools == {}


def test_project_report_stores_all_fields():
    command_result = CommandResult(
        command=["python", "--version"],
        available=True,
        output="Python 3.12.0",
        error=None,
    )
    check = CheckResult(name="readme", passed=True, score=10)
    report = ProjectReport(
        path="/tmp/project",
        score=85,
        status="Good",
        checks=[check],
        recommendations=["add ci"],
        detected_stack=["Python"],
        required_tools=["Docker"],
        available_tools={"python": command_result},
    )

    assert report.path == "/tmp/project"
    assert report.score == 85
    assert report.status == "Good"
    assert report.checks == [check]
    assert report.recommendations == ["add ci"]
    assert report.detected_stack == ["Python"]
    assert report.required_tools == ["Docker"]
    assert report.available_tools["python"] == command_result
