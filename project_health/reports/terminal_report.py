from __future__ import annotations

from collections.abc import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from project_health.models import ProjectReport


class TerminalReport:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def _join(self, items: list[str], empty_text: str = "None detected") -> str:
        if items:
            return ", ".join(items)
        return empty_text

    def _status_color(self, status: str) -> str:
        normalized = status.lower()
        if normalized == "critical":
            return "bold red"
        if normalized == "weak":
            return "bold yellow"
        if normalized == "good":
            return "bold green"
        if normalized == "excellent":
            return "bold bright_green"
        return "white"

    def _score_color(self, score: int) -> str:
        if score < 40:
            return "red"
        if score < 70:
            return "yellow"
        if score < 90:
            return "green"
        return "bright_green"

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

    def _result_text(self, passed: bool) -> Text:
        return Text("+" if passed else "-", style="green" if passed else "red")

    def _score_text(self, score: int) -> Text:
        return Text(str(score), style=self._score_color(score))

    def _issues_text(self, issues: list[str], passed: bool) -> Text:
        if not issues:
            return Text("-", style="dim")
        return Text(self._join(issues, empty_text="-"), style="yellow" if not passed else "default")

    def _score_bar(self, score: int, status_color: str, width: int = 20) -> Text:
        filled = round(score / 100 * width)
        filled = max(0, min(width, filled))

        bar = Text("[")
        bar.append("#" * filled, style=status_color)
        bar.append("-" * (width - filled), style="dim")
        bar.append("]")
        return bar

    def _status_meaning(self, status: str) -> str:
        meanings = {
            "critical": "not ready and has major problems.",
            "weak": "usable, but missing important metadata or documentation.",
            "good": "in good shape, with a few improvements still possible.",
            "excellent": "complete and well prepared.",
        }
        return meanings.get(status.lower(), "project status could not be determined.")

    def _header_panel(self, report: ProjectReport) -> Panel:
        status_color = self._status_color(report.status)
        content = Text()
        content.append(f"Path: {report.path}\n")
        content.append(f"Stack: {self._join(report.detected_stack)}\n")
        content.append(f"Score: {report.score}/100  ")
        content.append_text(self._score_bar(report.score, status_color))
        content.append("  ")
        content.append(report.status, style=status_color)
        return Panel.fit(
            content,
            title="Project Health Analyzer",
            border_style="dim",
        )

    def _has_any_dependencies(self, groups: Iterable[list[str]]) -> bool:
        return any(group for group in groups)

    def _print_tools(self, report: ProjectReport) -> None:
        self.console.print("[bold cyan]Tools[/bold cyan]")
        runtime_deps = self._python_dependencies(report, "dependencies")
        available_runtime_deps = self._available_python_packages(report, "available_packages")
        dev_deps = self._python_dependencies(report, "dev_dependencies")
        available_dev_deps = self._available_python_packages(report, "available_dev_packages")

        self.console.print(f"Required: {self._join(report.required_tools)}")
        self.console.print(f"Available: {self._join(list(report.available_tools.keys()))}")

        if not self._has_any_dependencies(
            (runtime_deps, available_runtime_deps, dev_deps, available_dev_deps)
        ):
            self.console.print("Dependencies: none detected")
            return

        if runtime_deps:
            self.console.print(f"Runtime deps: {self._join(runtime_deps)}")
        if available_runtime_deps:
            self.console.print(f"Available runtime deps: {self._join(available_runtime_deps)}")
        if dev_deps:
            self.console.print(f"Dev deps: {self._join(dev_deps)}")
        if available_dev_deps:
            self.console.print(f"Available dev deps: {self._join(available_dev_deps)}")

    def _print_status_meaning(self, report: ProjectReport) -> None:
        status_color = self._status_color(report.status)
        line = Text()
        line.append("Status", style="bold cyan")
        line.append("\n")
        line.append(report.status, style=status_color)
        line.append(" — ")
        line.append(self._status_meaning(report.status))
        self.console.print(line)

    def _sorted_checks(self, report: ProjectReport):
        return sorted(report.checks, key=lambda check: (check.passed, check.score, check.name.casefold()))

    def _print_checks(self, report: ProjectReport) -> None:
        self.console.print("[bold cyan]Checks[/bold cyan]")
        table = Table()
        table.add_column("Check")
        table.add_column("Result")
        table.add_column("Score")
        table.add_column("Issues")

        for check in self._sorted_checks(report):
            table.add_row(
                check.name.lower(),
                self._result_text(check.passed),
                self._score_text(check.score),
                self._issues_text(check.issues, check.passed),
            )

        self.console.print(table)

    def _print_recommendations(self, report: ProjectReport) -> None:
        self.console.print("[bold cyan]Recommendations[/bold cyan]")
        if not report.recommendations:
            self.console.print(Text("- No recommendations", style="green"))
            return

        for index, recommendation in enumerate(report.recommendations, start=1):
            line = Text()
            line.append(f"{index}. ", style="dim")
            line.append(recommendation, style="yellow")
            self.console.print(line)

    def render(self, report: ProjectReport) -> None:
        self.console.print(self._header_panel(report))
        self._print_tools(report)
        self._print_status_meaning(report)
        self._print_checks(report)
        self._print_recommendations(report)
