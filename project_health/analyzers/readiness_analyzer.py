from __future__ import annotations

from project_health.analyzers.recommendation_engine import RecommendationEngine
from project_health.models import CheckResult, ProjectReport, ScanFacts


class ReadinessAnalyzer:
    def __init__(
        self,
        recommendation_engine: RecommendationEngine | None = None,
    ) -> None:
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def analyze(self, facts: ScanFacts) -> ProjectReport:
        checks = facts.checks
        if checks:
            score = round(sum(check.score for check in checks) / len(checks))
        else:
            score = 0

        status = self._status(score)
        recommendations = self.recommendation_engine.collect(checks)
        recommendations.extend(self._compatibility_recommendations(facts))
        recommendations = self._deduplicate(recommendations)

        return ProjectReport(
            path=facts.path,
            score=score,
            status=status,
            checks=checks,
            recommendations=recommendations,
            detected_stack=facts.detected_stack,
            required_tools=facts.required_tools,
            available_tools=facts.available_tools,
        )

    def _empty_check(self, name: str) -> CheckResult:
        return CheckResult(
            name=name,
            passed=False,
            score=0,
            issues=["check was not executed"],
            recommendations=["implement this check"],
        )

    def _status(self, score: int) -> str:
        if score < 40:
            return "Critical"
        if score < 70:
            return "Weak"
        if score < 90:
            return "Good"
        return "Excellent"

    def _compatibility_recommendations(self, facts: ScanFacts) -> list[str]:
        recommendations: list[str] = []

        for tool in facts.required_tools:
            if tool not in facts.available_tools:
                recommendations.append(f"Install missing required tool: {tool}")

        return recommendations

    def _deduplicate(self, items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for item in items:
            cleaned = item.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            result.append(cleaned)

        return result
