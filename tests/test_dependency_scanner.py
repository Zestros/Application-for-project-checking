from pathlib import Path

from project_health.scanners.dependency_scanner import DependencyScanner


def test_python_requirements_txt_extracts_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi==0.110.0\ntyper>=0.12\n")

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert result.metadata["detected_stack"] == ["Python"]
    assert requirements["package_managers"] == ["pip"]
    assert requirements["required_tools"] == ["python", "pip"]
    assert requirements["dependencies"]["python"] == ["fastapi", "typer"]
    assert requirements["source_files"] == ["requirements.txt"]


def test_python_pyproject_toml_extracts_poetry_requirements(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.poetry]\n"
        'name = "demo"\n\n'
        "[tool.poetry.dependencies]\n"
        'python = ">=3.11"\n'
        'fastapi = "^0.110.0"\n\n'
        "[tool.poetry.group.dev.dependencies]\n"
        'pytest = "^9.0.0"\n'
    )

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert result.metadata["detected_stack"] == ["Python"]
    assert requirements["runtime"]["python"] == ">=3.11"
    assert requirements["package_managers"] == ["poetry"]
    assert requirements["required_tools"] == ["python", "poetry"]
    assert requirements["dependencies"]["python"] == ["fastapi"]
    assert requirements["dev_dependencies"]["python"] == ["pytest"]
    assert requirements["source_files"] == ["pyproject.toml"]


def test_python_version_file_sets_runtime_requirement(tmp_path: Path) -> None:
    (tmp_path / ".python-version").write_text("3.11.9\n")

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 70
    assert requirements["runtime"]["python"] == "3.11.9"
    assert requirements["runtime"]["python_version_file"] == "3.11.9"
    assert requirements["source_files"] == [".python-version"]


def test_requirements_dev_txt_uses_pip_package_manager(tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text("pytest==9.0.0\nruff\n")

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert requirements["package_managers"] == ["pip"]
    assert requirements["required_tools"] == ["python", "pip"]
    assert requirements["dev_dependencies"]["python"] == ["pytest", "ruff"]


def test_pep_621_pyproject_extracts_dependencies_and_dev_groups(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10"\n'
        'dependencies = ["FastAPI==0.110.0", "my_package>=1"]\n\n'
        "[project.optional-dependencies]\n"
        'dev = ["pytest"]\n'
        'lint = ["ruff"]\n'
    )

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert requirements["runtime"]["python"] == ">=3.10"
    assert requirements["runtime"]["requires_python"] == ">=3.10"
    assert requirements["package_managers"] == ["pip"]
    assert requirements["required_tools"] == ["python", "pip"]
    assert requirements["dependencies"]["python"] == ["fastapi", "my-package"]
    assert requirements["dev_dependencies"]["python"] == ["pytest", "ruff"]


def test_pipfile_extracts_dependencies(tmp_path: Path) -> None:
    (tmp_path / "Pipfile").write_text(
        "[packages]\n"
        'requests = "*"\n\n'
        "[dev-packages]\n"
        'pytest = "*"\n'
    )

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert requirements["package_managers"] == ["pipenv"]
    assert requirements["required_tools"] == ["python", "pipenv"]
    assert requirements["dependencies"]["python"] == ["requests"]
    assert requirements["dev_dependencies"]["python"] == ["pytest"]


def test_dockerfile_and_compose_are_detected(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\nWORKDIR /app\n")
    (tmp_path / "compose.yaml").write_text("services:\n  app:\n    build: .\n")

    result = DependencyScanner(tmp_path).scan()
    requirements = result.metadata["requirements"]

    assert result.passed is True
    assert result.score == 100
    assert result.metadata["detected_stack"] == ["Docker", "Docker Compose"]
    assert requirements["required_tools"] == ["docker", "docker compose"]
    assert requirements["source_files"] == ["Dockerfile", "compose.yaml"]
    assert requirements["docker"] == {
        "dockerfile": True,
        "compose": True,
        "base_images": ["python:3.11"],
    }


def test_multistage_dockerfile_collects_all_base_images(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text(
        "FROM --platform=linux/amd64 python:3.12-slim AS builder\n"
        "FROM debian:bookworm\n"
    )

    result = DependencyScanner(tmp_path).scan()
    docker = result.metadata["requirements"]["docker"]

    assert docker["base_images"] == ["python:3.12-slim", "debian:bookworm"]
