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

        return CheckResult(
            name="license",
            passed=True,
            score=100,
            metadata={"license_file": str(license_path)},
        )

    def _find_license(self) -> Path | None:
        for filename in self.LICENSE_FILENAMES:
            candidate = self.path / filename
            if candidate.is_file():
                return candidate

        return None
