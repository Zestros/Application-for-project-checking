import os
import re
from pathlib import Path
from typing import Any

from project_health.models import CheckResult, CommandResult
from project_health.utils.command_runner import run_command


class EnvScanner:
    DEFAULT_TOOLS = ("python", "pip", "docker")
    PACKAGE_MANAGERS = ("poetry", "pipenv", "uv", "hatch", "pdm", "flit", "rye")
    RECOMMENDATIONS = {
        "python": "Install required Python version or use pyenv/.venv",
        "pip": "Install pip or enable it with python -m ensurepip",
        "poetry": "Install Poetry or remove Poetry requirement",
        "pipenv": "Install Pipenv or remove Pipenv requirement",
        "uv": "Install uv or remove uv requirement",
        "hatch": "Install Hatch or remove Hatch requirement",
        "pdm": "Install PDM or remove PDM requirement",
        "flit": "Install Flit or remove Flit requirement",
        "rye": "Install Rye or remove Rye requirement",
        "docker": "Install Docker Desktop or Docker Engine",
        "docker compose": "Install Docker Compose or enable Docker Compose plugin",
    }

    def __init__(
        self,
        path: Path | str,
        requirements: dict[str, Any] | None = None,
        required_tools: list[str] | None = None,
    ) -> None:
        self.path = Path(path)
        self.requirements = requirements
        self.required_tools = required_tools

    def scan(self) -> CheckResult:
        metadata = self._empty_metadata()
        tools = self._tools_to_check()
        metadata["required_tools"] = tools

        for tool in tools:
            metadata["resolved_tools"][tool] = self._check_tool(tool, metadata)

        metadata["available_tools"] = [
            tool
            for tool, result in metadata["resolved_tools"].items()
            if result["available"]
        ]
        metadata["missing_tools"] = [
            tool
            for tool, result in metadata["resolved_tools"].items()
            if not result["available"]
        ]

        self._check_python_version(metadata)

        return self._result(metadata)

    def _empty_metadata(self) -> dict[str, Any]:
        return {
            "required_tools": [],
            "available_tools": [],
            "missing_tools": [],
            "resolved_tools": {},
            "version_mismatches": [],
            "commands": {},
        }

    def _tools_to_check(self) -> list[str]:
        if self.requirements is not None:
            tools = list(self.requirements.get("required_tools", []))
            tools.extend(self.requirements.get("package_managers", []))
        elif self.required_tools is not None:
            tools = list(self.required_tools)
        else:
            tools = list(self.DEFAULT_TOOLS)

        normalized_tools = []
        for tool in tools:
            if tool == "setuptools":
                continue
            normalized_tools.append(tool)

        return self._deduplicate(normalized_tools)

    def _check_tool(self, tool: str, metadata: dict[str, Any]) -> dict[str, Any]:
        if tool == "python":
            return self._check_python(metadata)
        if tool == "pip":
            return self._check_pip(metadata)
        if tool in self.PACKAGE_MANAGERS:
            if tool == "poetry":
                return self._check_poetry(metadata)
            if tool == "pipenv":
                return self._check_pipenv(metadata)
            return self._check_package_manager(tool, metadata)
        if tool == "docker":
            return self._check_docker(metadata)
        if tool == "docker compose":
            return self._check_docker_compose(metadata)

        return self._run_candidates(
            tool,
            [([tool, "--version"], "PATH", None)],
            metadata,
        )

    def _check_python(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._run_candidates(
            "python",
            self._candidate_python_commands(),
            metadata,
            version_extractor=self._extract_python_version,
        )

    def _check_pip(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._run_candidates(
            "pip",
            self._candidate_pip_commands(metadata),
            metadata,
        )

    def _check_package_manager(
        self,
        tool: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return self._run_candidates(
            tool,
            [([tool, "--version"], "PATH", None)],
            metadata,
        )

    def _check_poetry(self, metadata: dict[str, Any]) -> dict[str, Any]:
        result = self._check_package_manager("poetry", metadata)
        env_result = run_command(["poetry", "env", "info", "--path"])
        self._record_command("poetry", env_result, metadata)
        if env_result.available:
            result["env_path"] = env_result.output.strip()
        return result

    def _check_pipenv(self, metadata: dict[str, Any]) -> dict[str, Any]:
        result = self._check_package_manager("pipenv", metadata)
        venv_result = run_command(["pipenv", "--venv"])
        self._record_command("pipenv", venv_result, metadata)
        if venv_result.available:
            result["venv_path"] = venv_result.output.strip()
        return result

    def _check_docker(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._run_candidates(
            "docker",
            [(["docker", "--version"], "PATH", None)],
            metadata,
        )

    def _check_docker_compose(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._run_candidates(
            "docker compose",
            [
                (["docker", "compose", "version"], "docker compose", None),
                (["docker-compose", "--version"], "docker-compose", None),
            ],
            metadata,
        )

    def _candidate_python_commands(self) -> list[tuple[list[str], str, str | None]]:
        candidates: list[tuple[list[str], str, str | None]] = []
        venv_python = self.path / ".venv" / "bin" / "python"
        venv_windows_python = self.path / ".venv" / "Scripts" / "python.exe"

        candidates.append(
            ([str(venv_python), "--version"], ".venv", str(venv_python))
        )
        candidates.append(
            (
                [str(venv_windows_python), "--version"],
                ".venv",
                str(venv_windows_python),
            )
        )

        virtual_env = os.environ.get("VIRTUAL_ENV")
        if virtual_env:
            virtual_env_path = Path(virtual_env)
            virtual_env_python = virtual_env_path / "bin" / "python"
            virtual_env_windows_python = virtual_env_path / "Scripts" / "python.exe"
            candidates.append(
                (
                    [str(virtual_env_python), "--version"],
                    "VIRTUAL_ENV",
                    str(virtual_env_python),
                )
            )
            candidates.append(
                (
                    [str(virtual_env_windows_python), "--version"],
                    "VIRTUAL_ENV",
                    str(virtual_env_windows_python),
                )
            )

        if (self.path / ".python-version").is_file():
            candidates.append((["pyenv", "which", "python"], "pyenv", None))

        candidates.extend(
            [
                (["python", "--version"], "PATH", None),
                (["python3", "--version"], "PATH", None),
                (["python3.13", "--version"], "specific-python", None),
                (["python3.12", "--version"], "specific-python", None),
                (["python3.11", "--version"], "specific-python", None),
                (["python3.10", "--version"], "specific-python", None),
                (["python3.9", "--version"], "specific-python", None),
            ]
        )

        return candidates

    def _candidate_pip_commands(
        self,
        metadata: dict[str, Any],
    ) -> list[tuple[list[str], str, str | None]]:
        candidates: list[tuple[list[str], str, str | None]] = []
        python = metadata["resolved_tools"].get("python")

        if python and python["available"] and python["path"]:
            candidates.append(
                (
                    [python["path"], "-m", "pip", "--version"],
                    "python -m pip",
                    python["path"],
                )
            )

        venv_pip = self.path / ".venv" / "bin" / "pip"
        venv_windows_pip = self.path / ".venv" / "Scripts" / "pip.exe"
        candidates.append(([str(venv_pip), "--version"], ".venv", str(venv_pip)))
        candidates.append(
            ([str(venv_windows_pip), "--version"], ".venv", str(venv_windows_pip))
        )

        virtual_env = os.environ.get("VIRTUAL_ENV")
        if virtual_env:
            virtual_env_path = Path(virtual_env)
            virtual_env_pip = virtual_env_path / "bin" / "pip"
            virtual_env_windows_pip = virtual_env_path / "Scripts" / "pip.exe"
            candidates.append(
                ([str(virtual_env_pip), "--version"], "VIRTUAL_ENV", str(virtual_env_pip))
            )
            candidates.append(
                (
                    [str(virtual_env_windows_pip), "--version"],
                    "VIRTUAL_ENV",
                    str(virtual_env_windows_pip),
                )
            )

        candidates.append((["pip", "--version"], "PATH", None))
        candidates.append((["pip3", "--version"], "PATH", None))

        return candidates

    def _run_candidates(
        self,
        tool: str,
        candidates: list[tuple[list[str], str, str | None]],
        metadata: dict[str, Any],
        version_extractor: Any | None = None,
    ) -> dict[str, Any]:
        last_result: CommandResult | None = None

        for command, source, path in candidates:
            result = run_command(command)
            self._record_command(tool, result, metadata)
            last_result = result

            if source == "pyenv" and result.available:
                python_path = result.output.strip().splitlines()[0]
                pyenv_result = run_command([python_path, "--version"])
                self._record_command(tool, pyenv_result, metadata)
                if pyenv_result.available:
                    return self._resolved_tool(
                        True,
                        self._extract_python_version(pyenv_result.output),
                        source,
                        pyenv_result.command,
                        python_path,
                    )
                last_result = pyenv_result
                continue

            if result.available:
                extract = version_extractor or self._extract_version
                resolved_path = path or command[0]
                return self._resolved_tool(
                    True,
                    extract(result.output),
                    source,
                    command,
                    resolved_path,
                )

        fallback_command = candidates[-1][0] if candidates else [tool, "--version"]
        if last_result is not None:
            fallback_command = last_result.command

        return self._resolved_tool(False, None, "PATH", fallback_command, None)

    def _record_command(
        self,
        tool: str,
        result: CommandResult,
        metadata: dict[str, Any],
    ) -> None:
        metadata["commands"].setdefault(tool, []).append(self._command_to_dict(result))

    def _command_to_dict(self, result: CommandResult) -> dict[str, Any]:
        return {
            "command": result.command,
            "available": result.available,
            "output": result.output,
            "error": result.error,
        }

    def _resolved_tool(
        self,
        available: bool,
        version: str | None,
        source: str,
        command: list[str],
        path: str | None,
    ) -> dict[str, Any]:
        return {
            "available": available,
            "version": version,
            "source": source,
            "command": command,
            "path": path,
        }

    def _extract_version(self, output: str) -> str | None:
        match = re.search(r"(\d+(?:\.\d+){0,2})", output)
        if match:
            return match.group(1)
        return None

    def _extract_python_version(self, output: str) -> str | None:
        return self._extract_version(output)

    def _check_python_version(self, metadata: dict[str, Any]) -> None:
        required = self._python_requirement()
        python = metadata["resolved_tools"].get("python")

        if not required or not python or not python["available"] or not python["version"]:
            return

        if self._version_satisfies(python["version"], required):
            return

        metadata["version_mismatches"].append(
            {
                "tool": "python",
                "required": required,
                "found": python["version"],
                "source": python["source"],
            }
        )

    def _python_requirement(self) -> str | None:
        runtime = {}
        if self.requirements is not None:
            runtime = self.requirements.get("runtime", {})

        for key in ("python_version_file", "python", "requires_python"):
            value = runtime.get(key)
            if value:
                return str(value)

        version_file = self.path / ".python-version"
        if version_file.is_file():
            return version_file.read_text(encoding="utf-8", errors="ignore").strip()

        return None

    def _version_satisfies(self, found: str, required: str) -> bool:
        found_version = self._parse_version(found)
        required = required.replace(" ", "")

        if required.startswith("~="):
            base = self._parse_version(required[2:])
            upper = (base[0], base[1] + 1, 0)
            return (
                self._compare_versions(found_version, base) >= 0
                and self._compare_versions(found_version, upper) < 0
            )

        if required.startswith("^"):
            base = self._parse_version(required[1:])
            upper = (base[0] + 1, 0, 0)
            return (
                self._compare_versions(found_version, base) >= 0
                and self._compare_versions(found_version, upper) < 0
            )

        if any(required.startswith(operator) for operator in (">=", "<=", ">", "<")):
            for part in required.split(","):
                if part.startswith(">="):
                    if self._compare_versions(found_version, self._parse_version(part[2:])) < 0:
                        return False
                elif part.startswith("<="):
                    if self._compare_versions(found_version, self._parse_version(part[2:])) > 0:
                        return False
                elif part.startswith(">"):
                    if self._compare_versions(found_version, self._parse_version(part[1:])) <= 0:
                        return False
                elif part.startswith("<"):
                    if self._compare_versions(found_version, self._parse_version(part[1:])) >= 0:
                        return False
            return True

        required_version = self._parse_version(required)
        required_parts = [part for part in required.split(".") if part != ""]
        if len(required_parts) <= 2:
            return found_version[:2] == required_version[:2]
        return found_version == required_version

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        parts = re.findall(r"\d+", version)
        numbers = [int(part) for part in parts[:3]]
        while len(numbers) < 3:
            numbers.append(0)
        return numbers[0], numbers[1], numbers[2]

    def _compare_versions(
        self,
        left: tuple[int, int, int],
        right: tuple[int, int, int],
    ) -> int:
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def _result(self, metadata: dict[str, Any]) -> CheckResult:
        issues = [f"{tool} not found" for tool in metadata["missing_tools"]]
        recommendations = [
            self.RECOMMENDATIONS[tool]
            for tool in metadata["missing_tools"]
            if tool in self.RECOMMENDATIONS
        ]

        for mismatch in metadata["version_mismatches"]:
            issues.append(
                f"{mismatch['tool']} version mismatch: "
                f"required {mismatch['required']}, found {mismatch['found']}"
            )
            recommendations.append(
                f"Use Python {mismatch['required']} via .venv, pyenv, or system Python"
            )

        required_count = len(metadata["required_tools"])
        if required_count == 0:
            score = 100
        else:
            score = int(len(metadata["available_tools"]) / required_count * 100)

        score -= 20 * len(metadata["version_mismatches"])
        score = max(0, min(100, score))

        return CheckResult(
            name="Environment",
            passed=not metadata["missing_tools"] and not metadata["version_mismatches"],
            score=score,
            issues=self._deduplicate(issues),
            recommendations=self._deduplicate(recommendations),
            metadata=metadata,
        )

    def _deduplicate(self, items: list[Any]) -> list[Any]:
        deduplicated: list[Any] = []
        seen: set[Any] = set()

        for item in items:
            try:
                if item in seen:
                    continue
                seen.add(item)
            except TypeError:
                if item in deduplicated:
                    continue
            deduplicated.append(item)

        return deduplicated
