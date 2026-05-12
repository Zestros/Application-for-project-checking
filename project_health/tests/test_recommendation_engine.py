from project_health.analyzers.recommendation_engine import RecommendationEngine
from project_health.models import CheckResult


def test_collect_gathers_recommendations_from_multiple_checks():
    checks = [
        CheckResult(
            name="readme",
            passed=True,
            score=10,
            recommendations=["add badges", "write overview"],
        ),
        CheckResult(
            name="license",
            passed=False,
            score=0,
            recommendations=["add license"],
        ),
        CheckResult(
            name="ci",
            passed=False,
            score=0,
            recommendations=["configure ci"],
        ),
    ]

    result = RecommendationEngine().collect(checks)

    assert result == [
        "add badges",
        "write overview",
        "add license",
        "configure ci",
    ]


def test_collect_removes_duplicates_and_preserves_order():
    checks = [
        CheckResult(
            name="readme",
            passed=True,
            score=10,
            recommendations=["add badges", "write overview"],
        ),
        CheckResult(
            name="license",
            passed=False,
            score=0,
            recommendations=["add badges", "add license"],
        ),
    ]

    result = RecommendationEngine().collect(checks)

    assert result == [
        "add badges",
        "write overview",
        "add license",
    ]


def test_collect_ignores_empty_recommendations():
    checks = [
        CheckResult(
            name="readme",
            passed=True,
            score=10,
            recommendations=["", "   ", "add badges"],
        )
    ]

    result = RecommendationEngine().collect(checks)

    assert result == ["add badges"]


def test_collect_returns_empty_list_when_no_recommendations():
    checks = [
        CheckResult(name="readme", passed=True, score=10),
        CheckResult(name="license", passed=False, score=0),
    ]

    result = RecommendationEngine().collect(checks)

    assert result == []
