from __future__ import annotations

from rich.console import Console
from rich.table import Table

from project_health.models import ProjectReport


class TerminalReport:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def _join(self, items: list[str]) -> str:
        if items:
            return ", ".join(items)
        return "None detected"

    def _status_color(self, status: str) -> str:
        normalized = status.lower()
        if normalized == "critical":
            return "red"
        if normalized == "weak":
            return "yellow"
        if normalized == "good":
            return "green"
        if normalized == "excellent":
            return "bold green"
        return "white"

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

    def render(self, report: ProjectReport) -> None:
        self.console.print("[bold]Project health report[/bold]")
        self.console.print(f"Path: {report.path}")
        self.console.print(f"Score: {report.score}")

        status_color = self._status_color(report.status)
        self.console.print(f"Status: [{status_color}]{report.status}[/{status_color}]")

        self.console.print(f"Detected stack: {self._join(report.detected_stack)}")
        self.console.print(f"Required tools: {self._join(report.required_tools)}")
        self.console.print(f"Available tools: {self._join(list(report.available_tools.keys()))}")
        self.console.print(
            f"Runtime dependencies: {self._join(self._python_dependencies(report, 'dependencies'))}"
        )
        self.console.print(
            "Available runtime dependencies: "
            f"{self._join(self._available_python_packages(report, 'available_packages'))}"
        )
        self.console.print(
            f"Dev dependencies: {self._join(self._python_dependencies(report, 'dev_dependencies'))}"
        )
        self.console.print(
            "Available dev dependencies: "
            f"{self._join(self._available_python_packages(report, 'available_dev_packages'))}"
        )

        table = Table(title="Checks")
        table.add_column("Check")
        table.add_column("Passed")
        table.add_column("Score")
        table.add_column("Issues")
        table.add_column("Recommendations")

        for check in report.checks:
            table.add_row(
                check.name,
                "Yes" if check.passed else "No",
                str(check.score),
                self._join(check.issues),
                self._join(check.recommendations),
            )

        self.console.print(table)

        if report.recommendations:
            self.console.print("Recommendations:")
            for recommendation in report.recommendations:
                self.console.print(f"- {recommendation}")
