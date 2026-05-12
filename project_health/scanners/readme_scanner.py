from pathlib import Path

from project_health.models import CheckResult


class ReadmeScanner:
    README_FILENAMES = (
        "README",
        "README.md",
        "README.rst",
        "README.txt",
        "README.markdown",
    )

    REQUIRED_SECTIONS = {
        "description": (
            "description",
            "overview",
            "about",
            "what is",
            "описание",
            "обзор",
            "о проекте",
            "что это",
        ),
        "installation": (
            "installation",
            "install",
            "setup",
            "getting started",
            "установка",
            "установить",
            "настройка",
            "начало работы",
        ),
        "usage": (
            "usage",
            "quickstart",
            "example",
            "examples",
            "how to use",
            "использование",
            "быстрый старт",
            "пример",
            "примеры",
            "как использовать",
        ),
    }

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def scan(self) -> CheckResult:
        if not self.path.exists():
            return CheckResult(
                name="readme",
                passed=False,
                score=0,
                issues=["Project path does not exist"],
                recommendations=[],
                metadata={"readme_file": None},
            )

        if not self.path.is_dir():
            return CheckResult(
                name="readme",
                passed=False,
                score=0,
                issues=["Project path is not a directory"],
                recommendations=[],
                metadata={"readme_file": None},
            )

        readme_path = self._find_readme()

        if readme_path is None:
            return CheckResult(
                name="readme",
                passed=False,
                score=0,
                issues=["README file not found"],
                recommendations=["Add a README file to the project root"],
                metadata={"readme_file": None},
            )

        content = readme_path.read_text(encoding="utf-8", errors="ignore")
        stripped_content = content.strip()

        if not stripped_content:
            return CheckResult(
                name="readme",
                passed=False,
                score=10,
                issues=["README file is empty"],
                recommendations=[
                    "Add project description, installation instructions, and usage examples to README"
                ],
                metadata={
                    "readme_file": str(readme_path),
                    "found_sections": [],
                    "missing_sections": ["description", "installation", "usage"],
                },
            )

        found_sections = self._find_sections(content)
        missing_sections = [
            section
            for section in self.REQUIRED_SECTIONS
            if section not in found_sections
        ]

        score = 10
        if len(stripped_content) >= 100:
            score += 10
        if "description" in found_sections:
            score += 20
        if "installation" in found_sections:
            score += 30
        if "usage" in found_sections:
            score += 30
        score = min(score, 100)

        return CheckResult(
            name="readme",
            passed=score >= 60,
            score=score,
            issues=[
                f"Missing README section: {section}"
                for section in missing_sections
            ],
            recommendations=self._build_recommendations(missing_sections),
            metadata={
                "readme_file": str(readme_path),
                "found_sections": found_sections,
                "missing_sections": missing_sections,
                "size": len(content),
            },
        )

    def _find_readme(self) -> Path | None:
        root_files = {
            candidate.name.casefold(): candidate
            for candidate in self.path.iterdir()
            if candidate.is_file()
        }

        for filename in self.README_FILENAMES:
            candidate = root_files.get(filename.casefold())
            if candidate is not None:
                return candidate

        return None

    def _find_sections(self, content: str) -> list[str]:
        normalized_content = content.casefold()
        found_sections: list[str] = []

        for section, aliases in self.REQUIRED_SECTIONS.items():
            if any(alias in normalized_content for alias in aliases):
                found_sections.append(section)

        return found_sections

    def _build_recommendations(self, missing_sections: list[str]) -> list[str]:
        recommendation_by_section = {
            "description": "Add a short project description to README",
            "installation": "Add installation or setup instructions to README",
            "usage": "Add usage examples or quickstart instructions to README",
        }

        return [
            recommendation_by_section[section]
            for section in missing_sections
        ]
