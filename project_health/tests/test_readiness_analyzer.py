from project_health.analyzers.readiness_analyzer import ReadinessAnalyzer
from project_health.models import CheckResult, CommandResult, ScanFacts


def test_analyze_calculates_average_score_and_status():
    facts = ScanFacts(
        path="/tmp/project",
        checks=[
            CheckResult(name="a", passed=True, score=100),
            CheckResult(name="b", passed=True, score=50),
            CheckResult(name="c", passed=False, score=0),
        ],
    )

    report = ReadinessAnalyzer().analyze(facts)

    assert report.score == 50
    assert report.status == "Weak"


def test_analyze_transfers_scanfacts_data_to_project_report():
    check = CheckResult(name="readme", passed=True, score=10)
    command_result = CommandResult(
        command=["python", "--version"],
        available=True,
        output="Python 3.12.0",
        error=None,
    )
    facts = ScanFacts(
        path="/tmp/project",
        checks=[check],
        detected_stack=["Python"],
        required_tools=["python", "docker"],
        available_tools={"python": command_result},
    )

    report = ReadinessAnalyzer().analyze(facts)

    assert report.path == "/tmp/project"
    assert report.checks == [check]
    assert report.detected_stack == ["Python"]
    assert report.required_tools == ["python", "docker"]
    assert report.available_tools == {"python": command_result}


def test_analyze_collects_recommendations_from_checks():
    facts = ScanFacts(
        path="/tmp/project",
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
                recommendations=["add badges", "write overview"],
            )
        ],
    )

    report = ReadinessAnalyzer().analyze(facts)

    assert "add badges" in report.recommendations
    assert "write overview" in report.recommendations


def test_analyze_adds_missing_required_tools_recommendations():
    command_result = CommandResult(
        command=["python", "--version"],
        available=True,
        output="Python 3.12.0",
        error=None,
    )
    facts = ScanFacts(
        path="/tmp/project",
        checks=[],
        required_tools=["python", "pip", "docker"],
        available_tools={"python": command_result},
    )

    report = ReadinessAnalyzer().analyze(facts)

    assert "Install missing required tool: pip" in report.recommendations
    assert "Install missing required tool: docker" in report.recommendations


def test_analyze_deduplicates_recommendations():
    facts = ScanFacts(
        path="/tmp/project",
        checks=[
            CheckResult(
                name="readme",
                passed=True,
                score=10,
                recommendations=["add badges", "add badges"],
            ),
            CheckResult(
                name="license",
                passed=False,
                score=0,
                recommendations=["add badges"],
            ),
        ],
    )

    report = ReadinessAnalyzer().analyze(facts)

    assert report.recommendations == ["add badges"]


def test_analyze_with_empty_checks_returns_zero_score_and_critical_status():
    facts = ScanFacts(path="/tmp/project", checks=[])

    report = ReadinessAnalyzer().analyze(facts)

    assert report.score == 0
    assert report.status == "Critical"
    assert report.checks == []


def test_status_returns_expected_values():
    analyzer = ReadinessAnalyzer()

    assert analyzer._status(0) == "Critical"
    assert analyzer._status(39) == "Critical"
    assert analyzer._status(40) == "Weak"
    assert analyzer._status(69) == "Weak"
    assert analyzer._status(70) == "Good"
    assert analyzer._status(89) == "Good"
    assert analyzer._status(90) == "Excellent"
    assert analyzer._status(100) == "Excellent"


def test_empty_check_returns_default_check_result():
    analyzer = ReadinessAnalyzer()

    check = analyzer._empty_check("docker")

    assert check.name == "docker"
    assert check.passed is False
    assert check.score == 0
    assert check.issues
    assert check.recommendations
