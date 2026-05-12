from dataclasses import dataclass, field
from typing import Any

@dataclass
class CommandResult:
    command: list[str]
    available: bool
    output: str
    error: str | None


@dataclass
class CheckResult:
    name: str
    passed: bool
    score: int
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanFacts:
    path: str
    checks: list[CheckResult]
    detected_stack: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    available_tools: dict[str, CommandResult] = field(default_factory=dict)


@dataclass
class ProjectReport:
    path: str
    score: int
    status: str
    checks: list[CheckResult]
    recommendations: list[str] = field(default_factory=list)
    detected_stack: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    available_tools: dict[str, CommandResult] = field(default_factory=dict)
