from pathlib import Path

from project_health.models import CheckResult


class LicenseScanner:
    LICENSE_FILENAMES = (
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "LICENCE",
        "LICENCE.md",
        "LICENCE.txt",
        "COPYING",
        "COPYING.md",
        "COPYING.txt",
    )

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def scan(self) -> CheckResult:
        if not self.path.exists():
            return CheckResult(
                name="license",
                passed=False,
                score=0,
                issues=["Project path does not exist"],
                recommendations=[],
                metadata={"license_file": None},
            )

        if not self.path.is_dir():
            return CheckResult(
                name="license",
                passed=False,
                score=0,
                issues=["Project path is not a directory"],
                recommendations=[],
                metadata={"license_file": None},
            )

        license_path = self._find_license()

        if license_path is None:
            return CheckResult(
                name="license",
                passed=False,
                score=0,
                issues=["License file not found"],
                recommendations=["Add a LICENSE file to the project root"],
                metadata={"license_file": None},
            )

        if license_path.stat().st_size == 0:
            return CheckResult(
                name="license",
                passed=False,
                score=50,
                issues=["License file is empty"],
                recommendations=["Add the full license text to the LICENSE file"],
                metadata={"license_file": str(license_path)},
            )

        return CheckResult(
            name="license",
            passed=True,
            score=100,
            metadata={"license_file": str(license_path)},
        )

    def _find_license(self) -> Path | None:
        root_files = {
            candidate.name.casefold(): candidate
            for candidate in self.path.iterdir()
            if candidate.is_file()
        }

        for filename in self.LICENSE_FILENAMES:
            candidate = root_files.get(filename.casefold())
            if candidate is not None:
                return candidate

        return None
