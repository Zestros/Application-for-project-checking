from pathlib import Path

from project_health.scanners.license_scanner import LicenseScanner


def test_license_file_in_root_is_found(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is True
    assert result.score == 100
    assert result.metadata["license_file"].endswith("LICENSE")


def test_license_md_file_is_found(tmp_path: Path) -> None:
    (tmp_path / "LICENSE.md").write_text("MIT License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is True


def test_copying_file_is_found(tmp_path: Path) -> None:
    (tmp_path / "COPYING").write_text("GPL License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is True


def test_license_search_is_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / "License.TXT").write_text("MIT License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is True


def test_missing_license_returns_failed_result(tmp_path: Path) -> None:
    result = LicenseScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 0
    assert "License file not found" in result.issues
    assert result.metadata["license_file"] is None


def test_empty_license_file_returns_failed_result(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").touch()

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 50
    assert "License file is empty" in result.issues
    assert result.metadata["license_file"].endswith("LICENSE")


def test_missing_project_path_returns_failed_result(tmp_path: Path) -> None:
    result = LicenseScanner(tmp_path / "missing").scan()

    assert result.passed is False
    assert result.score == 0
    assert "Project path does not exist" in result.issues


def test_file_project_path_returns_failed_result(tmp_path: Path) -> None:
    project_file = tmp_path / "project.txt"
    project_file.write_text("not a directory\n")

    result = LicenseScanner(project_file).scan()

    assert result.passed is False
    assert result.score == 0
    assert "Project path is not a directory" in result.issues


def test_nested_license_file_is_not_found(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "LICENSE").write_text("MIT License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is False
    assert result.score == 0
    assert "License file not found" in result.issues


def test_multiple_license_files_use_license_filenames_order(tmp_path: Path) -> None:
    (tmp_path / "COPYING").write_text("GPL License\n")
    (tmp_path / "LICENSE").write_text("MIT License\n")

    result = LicenseScanner(tmp_path).scan()

    assert result.passed is True
    assert result.metadata["license_file"].endswith("LICENSE")
