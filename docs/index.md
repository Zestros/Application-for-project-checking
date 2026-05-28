# Project Health

Project Health is a command-line tool for checking whether a Python project is ready for review, submission, or further development.

The tool scans a target project directory and checks basic engineering artifacts:

- README and license files;
- Git repository metadata and `.gitignore`;
- dependency and build configuration files;
- required local tools such as Python, pip, Docker, and package managers;
- runtime and development package availability.

After scanning, Project Health returns a score, readiness status, detailed checks, and recommendations. The result can be printed as a terminal report or as JSON.

## Repository Parts

- `project_health/cli.py` contains the executable CLI entry point.
- `project_health/scanners/` collects facts about the target project.
- `project_health/analyzers/` calculates readiness and recommendations.
- `project_health/reports/` renders terminal and JSON output.
- `tests/` contains automated tests for CLI behavior, scanners, analyzers, models, and reports.
- `docs/diagrams/` contains editable Mermaid diagram sources.

## Common Commands

```bash
make install
make test
make coverage
make build
make run
make docs
make docker-build
make docker-run
```

