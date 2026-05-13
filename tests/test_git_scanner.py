from pathlib import Path

from project_health.scanners.git_scanner import GitScanner


def test_empty_directory_returns_failed_result(tmp_path: Path) -> None:
    result = GitScanner(tmp_path).scan()

    assert result.score == 0
    assert result.passed is False
    assert result.metadata["has_git"] is False
    assert result.metadata["has_gitignore"] is False
    assert "Git repository is not initialized" in result.issues
    assert ".gitignore is missing" in result.issues


def test_gitignore_only_scores_for_gitignore_and_patterns(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".env\n.venv/\n__pycache__/\n")

    result = GitScanner(tmp_path).scan()

    assert result.score == 50
    assert result.passed is True
    assert result.metadata["has_git"] is False
    assert result.metadata["has_gitignore"] is True
    assert result.metadata["gitignore_patterns"] == [".env", ".venv/", "__pycache__/"]


def test_git_only_scores_for_git_repository(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()

    result = GitScanner(tmp_path).scan()

    assert result.score == 50
    assert result.passed is True
    assert result.metadata["has_git"] is True
    assert result.metadata["has_gitignore"] is False


def test_git_and_normal_gitignore_get_full_score(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text(".env\n.venv/\n__pycache__/\nnode_modules/\n")

    result = GitScanner(tmp_path).scan()

    assert result.score == 100
    assert result.passed is True
    assert result.metadata["has_git"] is True
    assert result.metadata["has_gitignore"] is True


def test_empty_gitignore_reports_issue(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("# comment\n\n")

    result = GitScanner(tmp_path).scan()

    assert result.score == 90
    assert ".gitignore is empty" in result.issues
