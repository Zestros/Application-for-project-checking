from pathlib import Path

from project_health.models import CommandResult
from project_health.scanners import env_scanner
from project_health.scanners.env_scanner import EnvScanner


def command_result(
    command: list[str],
    available: bool,
    output: str = "",
    error: str | None = None,
) -> CommandResult:
    return CommandResult(
        command=command,
        available=available,
        output=output,
        error=error,
    )


def test_project_venv_python_has_priority(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        calls.append(command)
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["python"]).scan()
    python = result.metadata["resolved_tools"]["python"]

    assert result.passed is True
    assert calls[0] == [venv_python, "--version"]
    assert python["source"] == ".venv"
    assert python["path"] == venv_python
    assert python["version"] == "3.11.8"


def test_windows_venv_python_candidate_is_included(tmp_path: Path) -> None:
    commands = [
        command
        for command, _, _ in EnvScanner(tmp_path)._candidate_python_commands()
    ]

    assert [str(tmp_path / ".venv" / "Scripts" / "python.exe"), "--version"] in commands


def test_virtual_env_is_used_when_local_venv_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    virtual_env = tmp_path / "active-venv"
    virtual_env_python = str(virtual_env / "bin" / "python")
    monkeypatch.setenv("VIRTUAL_ENV", str(virtual_env))

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == [virtual_env_python, "--version"]:
            return command_result(command, True, "Python 3.12.1")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["python"]).scan()
    python = result.metadata["resolved_tools"]["python"]

    assert result.passed is True
    assert python["source"] == "VIRTUAL_ENV"
    assert python["path"] == virtual_env_python


def test_python_fallback_to_python3_works(tmp_path: Path, monkeypatch) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["python3", "--version"]:
            return command_result(command, True, "Python 3.11.8")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["python"]).scan()
    python = result.metadata["resolved_tools"]["python"]

    assert result.passed is True
    assert python["command"] == ["python3", "--version"]
    assert python["source"] == "PATH"


def test_pip_is_checked_through_found_python(tmp_path: Path, monkeypatch) -> None:
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        if command == [venv_python, "-m", "pip", "--version"]:
            return command_result(command, True, "pip 24.0")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["python", "pip"]).scan()
    pip = result.metadata["resolved_tools"]["pip"]

    assert result.passed is True
    assert pip["source"] == "python -m pip"
    assert pip["command"] == [venv_python, "-m", "pip", "--version"]
    assert pip["path"] == venv_python


def test_python_only_requirements_do_not_check_docker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command[0].endswith("python") or command[0] == "python":
            return command_result(command, True, "Python 3.11.8")
        if command[:3] == [command[0], "-m", "pip"]:
            return command_result(command, True, "pip 24.0")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={"required_tools": ["python", "pip"]},
    ).scan()

    assert result.passed is True
    assert "docker" not in result.metadata["commands"]
    assert result.metadata["missing_tools"] == []


def test_docker_only_requirements_do_not_check_python(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["docker", "--version"]:
            return command_result(command, True, "Docker version 27.0.0")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={"required_tools": ["docker"]},
    ).scan()

    assert result.passed is True
    assert "python" not in result.metadata["commands"]
    assert result.metadata["available_tools"] == ["docker"]


def test_missing_dependency_files_make_environment_fail(tmp_path: Path) -> None:
    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": [],
            "package_managers": [],
            "source_files": [],
        },
    ).scan()

    assert result.passed is False
    assert result.score == 0
    assert result.metadata["dependency_files_found"] is False
    assert result.issues == ["No dependency or build files found"]
    assert result.recommendations == ["Add dependency or build configuration files"]
    assert result.metadata["commands"] == {}


def test_docker_compose_falls_back_to_legacy_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["docker-compose", "--version"]:
            return command_result(command, True, "Docker Compose version v2.29.0")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["docker compose"]).scan()
    compose = result.metadata["resolved_tools"]["docker compose"]

    assert result.passed is True
    assert result.metadata["commands"]["docker compose"][0]["command"] == [
        "docker",
        "compose",
        "version",
    ]
    assert compose["command"] == ["docker-compose", "--version"]
    assert compose["source"] == "docker-compose"


def test_python_version_file_is_used_as_requirement(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / ".python-version").write_text("3.12\n")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command[0] == "pyenv":
            return command_result(command, False, error="not found")
        if command == ["python", "--version"]:
            return command_result(command, True, "Python 3.11.8")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["python"]).scan()

    assert result.passed is False
    assert result.metadata["version_mismatches"] == [
        {
            "tool": "python",
            "required": "3.12",
            "found": "3.11.8",
            "source": "PATH",
        }
    ]


def test_python_range_requirement_passes_for_compatible_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["python", "--version"]:
            return command_result(command, True, "Python 3.11.8")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python"],
            "runtime": {"python": ">=3.10,<3.13"},
        },
    ).scan()

    assert result.passed is True
    assert result.metadata["version_mismatches"] == []


def test_python_minimum_requirement_fails_for_old_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["python", "--version"]:
            return command_result(command, True, "Python 3.11.8")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python"],
            "runtime": {"python": ">=3.12"},
        },
    ).scan()

    assert result.passed is False
    assert result.score == 80
    assert "python version mismatch: required >=3.12, found 3.11.8" in result.issues


def test_poetry_is_checked_only_when_required(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        calls.append(command)
        if command == ["poetry", "--version"]:
            return command_result(command, True, "Poetry (version 1.8.0)")
        if command == ["poetry", "env", "info", "--path"]:
            return command_result(command, True, "/tmp/poetry-venv")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result_without_poetry = EnvScanner(tmp_path, required_tools=["python"]).scan()
    assert ["poetry", "--version"] not in calls

    calls.clear()
    result_with_poetry = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": [],
            "package_managers": ["poetry"],
        },
    ).scan()

    assert ["poetry", "--version"] in calls
    assert result_without_poetry.metadata["required_tools"] == ["python"]
    assert result_with_poetry.metadata["resolved_tools"]["poetry"]["available"] is True


def test_pipenv_is_checked_only_when_required(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        calls.append(command)
        if command == ["pipenv", "--version"]:
            return command_result(command, True, "pipenv, version 2024.0.0")
        if command == ["pipenv", "--venv"]:
            return command_result(command, True, "/tmp/pipenv-venv")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    EnvScanner(tmp_path, required_tools=["python"]).scan()
    assert ["pipenv", "--version"] not in calls

    calls.clear()
    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": [],
            "package_managers": ["pipenv"],
        },
    ).scan()

    assert ["pipenv", "--version"] in calls
    assert result.metadata["resolved_tools"]["pipenv"]["available"] is True


def test_setuptools_does_not_require_setuptools_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[list[str]] = []
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        calls.append(command)
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        if command == [venv_python, "-m", "pip", "--version"]:
            return command_result(command, True, "pip 24.0")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python", "pip"],
            "package_managers": ["setuptools"],
        },
    ).scan()

    assert result.passed is True
    assert result.metadata["required_tools"] == ["python", "pip"]
    assert not any(command[0] == "setuptools" for command in calls)


def test_missing_runtime_dependency_makes_environment_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        if command == [venv_python, "-m", "pip", "--version"]:
            return command_result(command, True, "pip 24.0")
        if command == [
            venv_python,
            "-c",
            "import importlib.metadata as m; m.version('rich')",
        ]:
            return command_result(command, False, error="PackageNotFoundError")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python", "pip"],
            "package_managers": ["pip"],
            "source_files": ["pyproject.toml"],
            "dependencies": {"python": ["rich"]},
            "dev_dependencies": {"python": []},
        },
    ).scan()

    assert result.passed is False
    assert result.score == 80
    assert result.metadata["missing_packages"] == ["rich"]
    assert result.metadata["missing_dev_packages"] == []
    assert result.issues == ["runtime dependency not installed: rich"]
    assert result.recommendations == ["Install declared runtime dependencies"]


def test_missing_dev_dependency_is_recommendation_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        if command == [venv_python, "-m", "pip", "--version"]:
            return command_result(command, True, "pip 24.0")
        if command == [
            venv_python,
            "-c",
            "import importlib.metadata as m; m.version('pytest')",
        ]:
            return command_result(command, False, error="PackageNotFoundError")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python", "pip"],
            "package_managers": ["pip"],
            "source_files": ["pyproject.toml"],
            "dependencies": {"python": []},
            "dev_dependencies": {"python": ["pytest"]},
        },
    ).scan()

    assert result.passed is True
    assert result.score == 100
    assert result.metadata["missing_packages"] == []
    assert result.metadata["missing_dev_packages"] == ["pytest"]
    assert result.issues == []
    assert result.recommendations == [
        "Install declared dev dependency when developing: pytest"
    ]


def test_available_python_packages_are_recorded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    venv_python = str(tmp_path / ".venv" / "bin" / "python")

    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == [venv_python, "--version"]:
            return command_result(command, True, "Python 3.11.8")
        if command == [venv_python, "-m", "pip", "--version"]:
            return command_result(command, True, "pip 24.0")
        if command == [
            venv_python,
            "-c",
            "import importlib.metadata as m; m.version('rich')",
        ]:
            return command_result(command, True, "15.0.0")
        if command == [
            venv_python,
            "-c",
            "import importlib.metadata as m; m.version('pytest')",
        ]:
            return command_result(command, True, "9.0.3")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(
        tmp_path,
        requirements={
            "required_tools": ["python", "pip"],
            "package_managers": ["pip"],
            "source_files": ["pyproject.toml"],
            "dependencies": {"python": ["rich"]},
            "dev_dependencies": {"python": ["pytest"]},
        },
    ).scan()

    assert result.metadata["available_packages"] == ["rich"]
    assert result.metadata["available_dev_packages"] == ["pytest"]
    assert result.metadata["missing_packages"] == []
    assert result.metadata["missing_dev_packages"] == []


def test_all_command_results_are_recorded(tmp_path: Path, monkeypatch) -> None:
    def fake_run(command: list[str], timeout: int = 5) -> CommandResult:
        if command == ["docker", "--version"]:
            return command_result(command, False, error="not found")
        return command_result(command, False, error="not found")

    monkeypatch.setattr(env_scanner, "run_command", fake_run)

    result = EnvScanner(tmp_path, required_tools=["docker"]).scan()

    assert result.passed is False
    assert result.metadata["commands"]["docker"] == [
        {
            "command": ["docker", "--version"],
            "available": False,
            "output": "",
            "error": "not found",
        }
    ]
