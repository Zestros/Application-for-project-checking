import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from project_health.models import CheckResult


class DependencyScanner:
    PYTHON_FILES = (
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        ".python-version",
    )
    COMPOSE_FILES = (
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    )
    PYPROJECT_TOOL_MANAGERS = {
        "hatch": "hatch",
        "pdm": "pdm",
        "uv": "uv",
        "flit": "flit",
        "rye": "rye",
        "setuptools": "setuptools",
    }
    PYPROJECT_BACKEND_MANAGERS = {
        "poetry": "poetry",
        "hatchling": "hatch",
        "pdm": "pdm",
        "flit": "flit",
        "setuptools": "setuptools",
    }

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def scan(self) -> CheckResult:
        issues: list[str] = []
        recommendations: list[str] = []
        metadata = self._empty_metadata()

        if not self.path.exists():
            issues.append("Project path does not exist")
            recommendations.append("Check the project path")
            return self._result(0, issues, recommendations, metadata)

        if not self.path.is_dir():
            issues.append("Project path is not a directory")
            recommendations.append("Provide a project directory path")
            return self._result(0, issues, recommendations, metadata)

        self._scan_python(metadata, issues)
        self._scan_docker(metadata, issues)

        requirements = metadata["requirements"]
        metadata["detected_stack"] = self._deduplicate(metadata["detected_stack"])
        requirements["package_managers"] = self._deduplicate(
            requirements["package_managers"]
        )
        requirements["required_tools"] = self._deduplicate(
            requirements["required_tools"]
        )
        requirements["lock_files"] = self._deduplicate(requirements["lock_files"])
        requirements["source_files"] = self._deduplicate(requirements["source_files"])

        if not requirements["source_files"]:
            issues.append("No known dependency or build files found")
            recommendations.append("Add dependency or build configuration files")

        python_without_package_manager = "Python" in metadata["detected_stack"] and not any(
            manager in requirements["package_managers"]
            for manager in (
                "pip",
                "poetry",
                "pipenv",
                "setuptools",
                "hatch",
                "pdm",
                "uv",
                "flit",
                "rye",
            )
        )
        if python_without_package_manager:
            issues.append("Python project detected but no package manager file found")
            recommendations.append("Add requirements.txt, pyproject.toml, or Pipfile")

        has_stack = bool(metadata["detected_stack"])
        has_tools = bool(requirements["required_tools"])
        if has_stack and has_tools and not python_without_package_manager:
            score = 100
        elif has_stack:
            score = 70
        else:
            score = 0

        return self._result(score, issues, recommendations, metadata)

    def _empty_metadata(self) -> dict[str, Any]:
        return {
            "detected_stack": [],
            "requirements": {
                "runtime": {},
                "package_managers": [],
                "required_tools": [],
                "dependencies": {
                    "python": [],
                },
                "dev_dependencies": {
                    "python": [],
                },
                "lock_files": [],
                "source_files": [],
                "docker": {
                    "dockerfile": False,
                    "compose": False,
                    "base_images": [],
                },
            },
        }

    def _result(
        self,
        score: int,
        issues: list[str],
        recommendations: list[str],
        metadata: dict[str, Any],
    ) -> CheckResult:
        return CheckResult(
            name="Dependencies",
            passed=score >= 70,
            score=score,
            issues=self._deduplicate(issues),
            recommendations=self._deduplicate(recommendations),
            metadata=metadata,
        )

    def _scan_python(self, metadata: dict[str, Any], issues: list[str]) -> None:
        requirements = metadata["requirements"]
        python_files = [
            filename
            for filename in self.PYTHON_FILES
            if self._has(filename)
        ]

        if not python_files:
            return

        metadata["detected_stack"].append("Python")
        requirements["required_tools"].append("python")
        requirements["source_files"].extend(python_files)

        if self._has("requirements.txt"):
            requirements["package_managers"].append("pip")
            requirements["required_tools"].append("pip")
            requirements["dependencies"]["python"].extend(
                self._read_requirements("requirements.txt", issues)
            )

        if self._has("requirements-dev.txt"):
            requirements["package_managers"].append("pip")
            requirements["required_tools"].append("pip")
            requirements["dev_dependencies"]["python"].extend(
                self._read_requirements("requirements-dev.txt", issues)
            )

        if self._has(".python-version"):
            version_lines = self._read_lines(".python-version", issues)
            if version_lines:
                requirements["runtime"]["python"] = version_lines[0]
                requirements["runtime"]["python_version_file"] = version_lines[0]

        if self._has("pyproject.toml"):
            pyproject = self._read_toml("pyproject.toml", issues)
            if pyproject:
                self._apply_pyproject(pyproject, metadata)

        if self._has("Pipfile"):
            requirements["package_managers"].append("pipenv")
            requirements["required_tools"].append("pipenv")
            pipfile = self._read_toml("Pipfile", issues)
            if pipfile:
                self._apply_pipfile(pipfile, metadata)

        if self._has("setup.py") or self._has("setup.cfg"):
            requirements["package_managers"].append("setuptools")
            requirements["required_tools"].append("pip")

        for lock_file in ("poetry.lock", "Pipfile.lock"):
            if self._has(lock_file):
                requirements["lock_files"].append(lock_file)
                if lock_file == "poetry.lock":
                    requirements["package_managers"].append("poetry")
                    requirements["required_tools"].append("poetry")
                if lock_file == "Pipfile.lock":
                    requirements["package_managers"].append("pipenv")
                    requirements["required_tools"].append("pipenv")

        requirements["dependencies"]["python"] = self._deduplicate(
            requirements["dependencies"]["python"]
        )
        requirements["dev_dependencies"]["python"] = self._deduplicate(
            requirements["dev_dependencies"]["python"]
        )

    def _scan_docker(self, metadata: dict[str, Any], issues: list[str]) -> None:
        requirements = metadata["requirements"]
        docker = requirements["docker"]
        compose_files = [
            filename
            for filename in self.COMPOSE_FILES
            if self._has(filename)
        ]

        if self._has("Dockerfile"):
            metadata["detected_stack"].append("Docker")
            requirements["required_tools"].append("docker")
            requirements["source_files"].append("Dockerfile")
            docker["dockerfile"] = True
            docker["base_images"].extend(self._docker_base_images("Dockerfile", issues))

        if compose_files:
            metadata["detected_stack"].append("Docker Compose")
            requirements["required_tools"].append("docker")
            requirements["required_tools"].append("docker compose")
            requirements["source_files"].extend(compose_files)
            docker["compose"] = True

        docker["base_images"] = self._deduplicate(docker["base_images"])

    def _apply_pyproject(
        self,
        pyproject: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        requirements = metadata["requirements"]
        project = pyproject.get("project", {})
        tool = pyproject.get("tool", {})
        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}

        if isinstance(project, dict):
            if project.get("requires-python"):
                requirements["runtime"]["requires_python"] = project["requires-python"]
                requirements["runtime"].setdefault("python", project["requires-python"])
            requirements["dependencies"]["python"].extend(
                self._requirement_name(dependency)
                for dependency in project.get("dependencies", [])
            )
            optional_dependencies = project.get("optional-dependencies", {})
            if isinstance(optional_dependencies, dict):
                for group_name in ("dev", "test", "tests", "lint"):
                    dependencies = optional_dependencies.get(group_name, [])
                    requirements["dev_dependencies"]["python"].extend(
                        self._requirement_name(dependency)
                        for dependency in dependencies
                    )
            if project.get("dependencies") or optional_dependencies:
                requirements["package_managers"].append("pip")
                requirements["required_tools"].append("pip")

        if isinstance(tool, dict):
            for tool_name, manager in self.PYPROJECT_TOOL_MANAGERS.items():
                if tool_name in tool:
                    requirements["package_managers"].append(manager)
                    if manager != "setuptools":
                        requirements["required_tools"].append(manager)

        build_system = pyproject.get("build-system", {})
        if isinstance(build_system, dict):
            build_backend = str(build_system.get("build-backend", ""))
            for backend_name, manager in self.PYPROJECT_BACKEND_MANAGERS.items():
                if backend_name in build_backend:
                    requirements["package_managers"].append(manager)
                    if manager != "setuptools":
                        requirements["required_tools"].append(manager)

        if isinstance(poetry, dict) and poetry:
            requirements["package_managers"].append("poetry")
            requirements["required_tools"].append("poetry")
            dependencies = poetry.get("dependencies", {})
            if isinstance(dependencies, dict):
                python_version = dependencies.get("python")
                if python_version and "python" not in requirements["runtime"]:
                    requirements["runtime"]["python"] = str(python_version)
                if python_version:
                    requirements["runtime"].setdefault(
                        "requires_python",
                        str(python_version),
                    )
                requirements["dependencies"]["python"].extend(
                    name for name in dependencies if name != "python"
                )

            dev_dependencies = poetry.get("dev-dependencies", {})
            if isinstance(dev_dependencies, dict):
                requirements["dev_dependencies"]["python"].extend(
                    dev_dependencies.keys()
                )

            groups = poetry.get("group", {})
            if isinstance(groups, dict):
                for group in groups.values():
                    if not isinstance(group, dict):
                        continue
                    group_dependencies = group.get("dependencies", {})
                    if isinstance(group_dependencies, dict):
                        requirements["dev_dependencies"]["python"].extend(
                            group_dependencies.keys()
                        )

    def _apply_pipfile(
        self,
        pipfile: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        requirements = metadata["requirements"]
        packages = pipfile.get("packages", {})
        dev_packages = pipfile.get("dev-packages", {})

        if isinstance(packages, dict):
            requirements["dependencies"]["python"].extend(packages.keys())

        if isinstance(dev_packages, dict):
            requirements["dev_dependencies"]["python"].extend(dev_packages.keys())

    def _read_toml(self, filename: str, issues: list[str]) -> dict[str, Any] | None:
        if tomllib is None:
            issues.append("TOML parsing is not available")
            return None

        path = self.path / filename
        try:
            return tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            issues.append(f"Could not read or parse {filename}: {error}")
            return None

    def _read_lines(self, filename: str, issues: list[str]) -> list[str]:
        path = self.path / filename
        try:
            return [
                line.strip()
                for line in path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        except OSError as error:
            issues.append(f"Could not read {filename}: {error}")
            return []

    def _read_requirements(self, filename: str, issues: list[str]) -> list[str]:
        requirements: list[str] = []

        for line in self._read_lines(filename, issues):
            if line.startswith("--"):
                continue

            requirement_name = self._requirement_name(line)
            if requirement_name:
                requirements.append(requirement_name)

        return requirements

    def _docker_base_images(self, filename: str, issues: list[str]) -> list[str]:
        base_images: list[str] = []

        for line in self._read_lines(filename, issues):
            parts = line.split()
            if parts and parts[0].casefold() == "from" and len(parts) >= 2:
                for part in parts[1:]:
                    if not part.startswith("--"):
                        base_images.append(part)
                        break

        return base_images

    def _requirement_name(self, requirement: str) -> str:
        if "#egg=" in requirement:
            return self._normalize_dependency_name(
                requirement.rsplit("#egg=", 1)[1].split("&", 1)[0]
            )

        requirement = requirement.split("#", 1)[0].strip()
        if requirement.startswith("-e "):
            requirement = requirement[3:].strip()
        if requirement in (".", ".[dev]") or requirement.startswith(("./", "../")):
            return ""

        match = re.match(r"([A-Za-z0-9_.-]+)", requirement)
        if match:
            return self._normalize_dependency_name(match.group(1))
        return requirement

    def _has(self, filename: str) -> bool:
        return (self.path / filename).is_file()

    def _normalize_dependency_name(self, name: str) -> str:
        return re.sub(r"[-_.]+", "-", name).lower()

    def _deduplicate(self, items: list[Any]) -> list[Any]:
        deduplicated: list[Any] = []

        for item in items:
            if item not in deduplicated:
                deduplicated.append(item)

        return deduplicated
