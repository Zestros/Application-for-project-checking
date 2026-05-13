from pathlib import Path

from project_health.models import CheckResult
from project_health.scanners import project_scanner
from project_health.scanners.project_scanner import ProjectScanner


def check(name: str) -> CheckResult:
    return CheckResult(name=name, passed=True, score=100)


def test_project_scanner_exposes_available_environment_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeDependencyScanner:
        def __init__(self, path: Path) -> None:
            self.path = path

        def scan(self) -> CheckResult:
            return CheckResult(
                name="Dependencies",
                passed=True,
                score=100,
                metadata={
                    "detected_stack": ["Python"],
                    "requirements": {
                        "required_tools": ["python", "pip"],
                        "package_managers": ["pip"],
                        "source_files": ["pyproject.toml"],
                    },
                },
            )

    class FakeEnvScanner:
        def __init__(self, path: Path, requirements: dict) -> None:
            self.path = path
            self.requirements = requirements

        def scan(self) -> CheckResult:
            return CheckResult(
                name="Environment",
                passed=True,
                score=100,
                metadata={
                    "available_tools": ["python", "pip"],
                    "resolved_tools": {
                        "python": {
                            "available": True,
                            "command": ["python", "--version"],
                        },
                        "pip": {
                            "available": True,
                            "command": ["python", "-m", "pip", "--version"],
                        },
                    },
                    "commands": {
                        "python": [
                            {
                                "command": ["python", "--version"],
                                "available": True,
                                "output": "Python 3.11.9",
                                "error": None,
                            }
                        ],
                        "pip": [
                            {
                                "command": ["python", "-m", "pip", "--version"],
                                "available": True,
                                "output": "pip 24.0",
                                "error": None,
                            }
                        ],
                    },
                },
            )

    class FakeScanner:
        def __init__(self, path: Path) -> None:
            self.path = path

        def scan(self) -> CheckResult:
            return check(self.__class__.__name__)

    monkeypatch.setattr(project_scanner, "DependencyScanner", FakeDependencyScanner)
    monkeypatch.setattr(project_scanner, "EnvScanner", FakeEnvScanner)
    monkeypatch.setattr(project_scanner, "ReadmeScanner", FakeScanner)
    monkeypatch.setattr(project_scanner, "LicenseScanner", FakeScanner)
    monkeypatch.setattr(project_scanner, "GitScanner", FakeScanner)

    facts = ProjectScanner(tmp_path).scan()

    assert facts.detected_stack == ["Python"]
    assert facts.required_tools == ["python", "pip"]
    assert set(facts.available_tools) == {"python", "pip"}
    assert facts.available_tools["python"].output == "Python 3.11.9"
    assert facts.available_tools["pip"].output == "pip 24.0"
