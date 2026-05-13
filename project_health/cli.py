from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

import typer

from project_health import __version__

app = typer.Typer(help="Project health checks CLI.")


def _import_symbol(module_path: str, symbol_name: str) -> Any:
    module = import_module(module_path)
    return getattr(module, symbol_name)


def _load_scanner() -> Any:
    return _import_symbol("project_health.scanners.project_scanner", "ProjectScanner")


def _load_analyzer() -> Any:
    candidates = (
        "project_health.analyzers.readiness_analyzer",
        "project_health.readiness_analyzer",
        "project_health.analyzer",
    )
    for module_path in candidates:
        try:
            return _import_symbol(module_path, "ReadinessAnalyzer")
        except (ImportError, AttributeError):
            continue
    raise RuntimeError("ReadinessAnalyzer is not available.")


def _load_renderer(output_format: str) -> Any:
    renderers = {
        "json": ("project_health.reports.json_report", "JsonReport"),
        "terminal": ("project_health.reports.terminal_report", "TerminalReport"),
    }
    module_path, symbol_name = renderers[output_format]
    return _import_symbol(module_path, symbol_name)


def _emit_report(renderer: Any, report: Any) -> None:
    if hasattr(renderer, "render"):
        rendered = renderer.render(report)
    else:
        rendered = renderer(report)

    if rendered is not None:
        typer.echo(rendered)


@app.command()
def scan(
    path: Path = typer.Argument(..., exists=False, dir_okay=True, file_okay=True, readable=True),
    output_format: str = typer.Option(
        "terminal",
        "--output-format",
        "-o",
        case_sensitive=False,
        help="Output format: terminal or json.",
    ),
) -> None:
    normalized_format = output_format.lower()
    if normalized_format not in {"terminal", "json"}:
        raise typer.BadParameter("output_format must be 'terminal' or 'json'.")

    if not path.exists():
        raise typer.BadParameter(f"Path does not exist: {path}")

    project_scanner = _load_scanner()(path)
    scan_facts = project_scanner.scan()
    project_report = _load_analyzer()().analyze(scan_facts)
    renderer = _load_renderer(normalized_format)()
    _emit_report(renderer, project_report)


@app.command()
def version() -> None:
    typer.echo(f"project-health {__version__}")


if __name__ == "__main__":
    app()
