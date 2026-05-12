from __future__ import annotations

from project_health.models import CheckResult


class RecommendationEngine:
    def collect(self, checks: list[CheckResult]) -> list[str]:
        recommendations: list[str] = []
        seen: set[str] = set()

        for check in checks:
            for recommendation in check.recommendations:
                cleaned = recommendation.strip()
                if not cleaned or cleaned in seen:
                    continue
                seen.add(cleaned)
                recommendations.append(cleaned)

        return recommendations
