# Architecture

Project Health is organized as a reusable Python package with a CLI application on top of it.

The executable application is the `pha` command, defined by the package entry point in `pyproject.toml`. The reusable implementation lives in the `project_health` package and can be imported by tests or future integrations.

## Layers

### CLI Layer

`project_health.cli` owns command-line input and output orchestration.

It validates the target path and output format, then delegates the real work to scanners, analyzers, and report renderers.

### Scanning Layer

`project_health.scanners` collects facts from the target project.

The main coordinator is `ProjectScanner`. It combines specialized scanners:

- `ReadmeScanner`;
- `LicenseScanner`;
- `GitScanner`;
- `DependencyScanner`;
- `EnvScanner`.

This layer reads files and checks the local environment, but it does not decide the final readiness status.

### Analysis Layer

`project_health.analyzers` converts scan facts into a project readiness report.

`ReadinessAnalyzer` calculates the total score and status. `RecommendationEngine` turns failed or weak checks into actionable recommendations.

### Reporting Layer

`project_health.reports` renders the final report.

`TerminalReport` creates a human-readable terminal view. `JsonReport` creates machine-readable JSON output from the same report model.

### Shared Models

`project_health.models` defines the data structures passed between layers:

- `CommandResult`;
- `CheckResult`;
- `ScanFacts`;
- `ProjectReport`.

## Data Flow

1. The user runs `pha scan <path>`.
2. The CLI validates the path and output format.
3. `ProjectScanner` runs specialized scanners.
4. The scanners return `ScanFacts`.
5. `ReadinessAnalyzer` converts facts into `ProjectReport`.
6. The selected renderer prints terminal output or JSON.

## Reproducibility Decisions

- Python version is fixed in `.python-version`.
- Runtime and development dependencies are declared in `pyproject.toml`.
- Common commands are exposed through `Makefile`.
- The CLI can be installed into a local `.venv` with `make install`.
- The package can be built with `make build`.
- The CLI can be run in a container with the provided `Dockerfile`.

