from pathlib import Path

from project_health.scanners.readme_scanner import ReadmeScanner


def test_missing_project_path_returns_failed_result(tmp_path: Path) -> None:
    result = ReadmeScanner(tmp_path / "missing").scan()

    assert result.passed is False
    assert result.score == 0
    assert "Project path does not exist" in result.issues
    assert result.metadata["readme_file"] is None


def test_file_project_path_returns_failed_result(tmp_path: Path) -> None:
    project_file = tmp_path / "project.txt"
    project_file.write_text("not a directory\n")

    result = ReadmeScanner(project_file).scan()

    assert result.passed is False
    assert result.score == 0
    assert "Project path is not a directory" in result.issues
    assert result.metadata["readme_file"] is None


def test_missing_readme_returns_failed_result(tmp_path: Path) -> None:
    result = ReadmeScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 0
    assert "README file not found" in result.issues
    assert result.metadata["readme_file"] is None


def test_readme_file_is_found_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / "ReadMe.MD").write_text("Description\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.metadata["readme_file"].endswith("ReadMe.MD")


def test_alternative_readme_filename_is_found(tmp_path: Path) -> None:
    (tmp_path / "README.rst").write_text("Description\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.metadata["readme_file"].endswith("README.rst")


def test_empty_readme_returns_failed_result(tmp_path: Path) -> None:
    (tmp_path / "README.md").touch()

    result = ReadmeScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 10
    assert "README file is empty" in result.issues
    assert result.metadata["found_sections"] == []
    assert result.metadata["missing_sections"] == [
        "description",
        "installation",
        "usage",
    ]


def test_readme_with_description_installation_and_usage_passes(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Project\n\n"
        "Description\nThis project checks repository health and documentation quality.\n\n"
        "Installation\nInstall dependencies and run the scanner from your terminal.\n\n"
        "Usage\nUse the command line interface with a project path to generate a report.\n"
    )

    result = ReadmeScanner(tmp_path).scan()

    assert result.passed is True
    assert result.score == 100
    assert result.issues == []
    assert result.recommendations == []
    assert result.metadata["found_sections"] == [
        "description",
        "installation",
        "usage",
    ]
    assert result.metadata["missing_sections"] == []


def test_readme_without_description_reports_partial_result(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Installation\nUsage\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.passed is True
    assert result.score == 70
    assert result.metadata["found_sections"] == ["installation", "usage"]
    assert result.metadata["missing_sections"] == ["description"]
    assert "Missing README section: description" in result.issues
    assert "Add a short project description to README" in result.recommendations


def test_readme_with_only_description_fails(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Description\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 30
    assert result.metadata["found_sections"] == ["description"]
    assert result.metadata["missing_sections"] == ["installation", "usage"]
    assert "Missing README section: installation" in result.issues
    assert "Missing README section: usage" in result.issues


def test_russian_sections_are_found(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Проект\n\n"
        "Описание\nКраткое описание проекта.\n\n"
        "Установка\nКак установить проект.\n\n"
        "Использование\nПример запуска.\n"
    )

    result = ReadmeScanner(tmp_path).scan()

    assert result.metadata["found_sections"] == [
        "description",
        "installation",
        "usage",
    ]


def test_readme_section_case_does_not_matter(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("DESCRIPTION\nINSTALLATION\nUsage\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.metadata["found_sections"] == [
        "description",
        "installation",
        "usage",
    ]


def test_short_readme_does_not_receive_length_bonus(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Description\nInstallation\nUsage\n")

    result = ReadmeScanner(tmp_path).scan()

    assert result.score == 90
    assert result.passed is True
