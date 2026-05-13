from pathlib import Path

from project_health.models import CheckResult


class GitScanner:
    RECOMMENDED_PATTERNS = (
        ".env",
        ".venv/",
        "__pycache__/",
        "dist/",
        "build/",
        "*.pyc",
    )

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def scan(self) -> CheckResult:
        git_path = self.path / ".git"
        gitignore_path = self.path / ".gitignore"

        has_git = git_path.exists() and (git_path.is_dir() or git_path.is_file())
        has_gitignore = gitignore_path.is_file()
        gitignore_patterns = self._read_gitignore_patterns(gitignore_path)
        found_recommended_patterns = [
            pattern
            for pattern in self.RECOMMENDED_PATTERNS
            if pattern in gitignore_patterns
        ]
        missing_recommended_patterns = [
            pattern
            for pattern in self.RECOMMENDED_PATTERNS
            if pattern not in gitignore_patterns
        ]

        score = 0
        if has_git:
            score += 50
        if has_gitignore:
            score += 40
        if gitignore_patterns and found_recommended_patterns:
            score += 10

        issues: list[str] = []
        recommendations: list[str] = []

        if not has_git:
            issues.append("Git repository is not initialized")
            recommendations.append("Initialize git for the project")

        if not has_gitignore:
            issues.append(".gitignore is missing")
            recommendations.append("Add a .gitignore file")
        elif not gitignore_patterns:
            issues.append(".gitignore is empty")
            recommendations.append("Add common ignore patterns to .gitignore")
        elif not found_recommended_patterns:
            issues.append(".gitignore does not include common recommended patterns")
            recommendations.append("Add common ignore patterns to .gitignore")

        return CheckResult(
            name="git",
            passed=score >= 50,
            score=score,
            issues=issues,
            recommendations=recommendations,
            metadata={
                "has_git": has_git,
                "has_gitignore": has_gitignore,
                "gitignore_patterns": gitignore_patterns,
                "missing_recommended_patterns": missing_recommended_patterns,
            },
        )

    def _read_gitignore_patterns(self, gitignore_path: Path) -> list[str]:
        if not gitignore_path.is_file():
            return []

        patterns: list[str] = []

        for line in gitignore_path.read_text().splitlines():
            pattern = line.strip()
            if pattern and not pattern.startswith("#"):
                patterns.append(pattern)

        return patterns
