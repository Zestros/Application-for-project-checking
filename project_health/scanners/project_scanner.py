from pathlib import Path

from project_health.models import ScanFacts
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

        checks = [
            ReadmeScanner(self.path).scan(),
            LicenseScanner(self.path).scan(),
            GitScanner(self.path).scan(),
            dependency_check,
            EnvScanner(self.path, requirements=requirements).scan(),
        ]

        return ScanFacts(
            path=str(self.path),
            checks=checks,
            detected_stack=dependency_check.metadata.get("detected_stack", []),
            required_tools=requirements.get("required_tools", []),
            available_tools={},
        )
