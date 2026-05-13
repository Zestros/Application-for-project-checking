from __future__ import annotations

import json
from dataclasses import asdict

from project_health.models import ProjectReport


class JsonReport:
    def _python_dependencies(self, report: ProjectReport, group: str) -> list[str]:
        for check in report.checks:
            if check.name != "Dependencies":
                continue
            requirements = check.metadata.get("requirements", {})
            dependencies = requirements.get(group, {})
            return dependencies.get("python", [])
        return []

    def _available_python_packages(
        self,
        report: ProjectReport,
        metadata_key: str,
    ) -> list[str]:
        for check in report.checks:
            if check.name != "Environment":
                continue
            return check.metadata.get(metadata_key, [])
        return []

    def render(self, report: ProjectReport) -> str:
        payload = asdict(report)
        payload["runtime_dependencies"] = self._python_dependencies(
            report,
            "dependencies",
        )
        payload["available_runtime_dependencies"] = self._available_python_packages(
            report,
            "available_packages",
        )
        payload["dev_dependencies"] = self._python_dependencies(
            report,
            "dev_dependencies",
        )
        payload["available_dev_dependencies"] = self._available_python_packages(
            report,
            "available_dev_packages",
        )

        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
