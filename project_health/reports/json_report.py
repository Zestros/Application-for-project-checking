from __future__ import annotations

import json
from dataclasses import asdict

from project_health.models import ProjectReport


class JsonReport:
    def render(self, report: ProjectReport) -> str:
        return json.dumps(
            asdict(report),
            ensure_ascii=False,
            indent=2,
        )
