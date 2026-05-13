from pathlib import Path

from project_health.models import CommandResult, ScanFacts
from project_health.scanners.dependency_scanner import DependencyScanner
from project_health.scanners.env_scanner import EnvScanner
from project_health.scanners.git_scanner import GitScanner
from project_health.scanners.license_scanner import LicenseScanner
from project_health.scanners.readme_scanner import ReadmeScanner


class ProjectScanner:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def scan(self) -> ScanFacts:
        dependency_check = DependencyScanner(self.path).scan()
        requirements = dependency_check.metadata.get("requirements", {})
        env_check = EnvScanner(self.path, requirements=requirements).scan()

        checks = [
            ReadmeScanner(self.path).scan(),
            LicenseScanner(self.path).scan(),
            GitScanner(self.path).scan(),
            dependency_check,
            env_check,
        ]

        return ScanFacts(
            path=str(self.path),
            checks=checks,
            detected_stack=dependency_check.metadata.get("detected_stack", []),
            required_tools=requirements.get("required_tools", []),
            available_tools=self._available_tools(env_check),
        )

    def _available_tools(self, env_check) -> dict[str, CommandResult]:
        metadata = env_check.metadata
        available_tools = {}

        for tool in metadata.get("available_tools", []):
            command = self._resolved_command(tool, metadata)
            if command is not None:
                available_tools[tool] = command

        return available_tools

    def _resolved_command(
        self,
        tool: str,
        metadata: dict,
    ) -> CommandResult | None:
        resolved = metadata.get("resolved_tools", {}).get(tool)
        if not resolved:
            return None

        for command in metadata.get("commands", {}).get(tool, []):
            if command["command"] == resolved["command"]:
                return CommandResult(
                    command=command["command"],
                    available=command["available"],
                    output=command["output"],
                    error=command["error"],
                )

        return CommandResult(
            command=resolved["command"],
            available=resolved["available"],
            output="",
            error=None,
        )
