# project-health

`project-health` is a CLI utility for checking the health of a Python project. It scans a repository, looks for core infrastructure files, detects the stack and dependency setup, checks whether the required environment tools are available, and generates a final report with a score and recommendations.

## Main Features

- checks whether a `README` file exists and whether it contains core sections;
- checks whether a license file exists;
- checks whether `.git` exists and whether `.gitignore` contains common patterns;
- analyzes dependency and build files such as `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `Pipfile`, `setup.py`, `setup.cfg`, `.python-version`, `Dockerfile`, `compose.yaml`, and related variants;
- detects required environment tools, including `python`, `pip`, `poetry`, `pipenv`, `uv`, `hatch`, `pdm`, `flit`, `rye`, `docker`, and `docker compose`;
- tries to find a suitable Python interpreter via `.venv`, `VIRTUAL_ENV`, `pyenv`, and system commands;
- compares the detected Python version against the project requirements;
- renders the report in terminal or JSON format.

## Project Structure

```text
project_health/
  cli.py                   # CLI commands: scan and version
  models.py                # scan result and report models
  analyzers/               # score calculation and recommendation logic
  scanners/                # README, license, git, dependency, and environment checks
  reports/                 # terminal and JSON report renderers
  utils/command_runner.py  # external command execution
tests/                     # tests for CLI, scanners, analyzers, and reports
pyproject.toml             # dependencies, pytest config, and CLI entry point
README.md
```

## Requirements

- Python `>=3.11`;
- `pip` for installing dependencies;
- for full environment checks, the target project may require tools such as `python`, `pip`, `poetry`, `pipenv`, `docker`, or `docker compose` depending on its configuration.

## Installation

Clone the repository and install the package locally:

```bash
git clone <repository-url>
cd Application-for-project-checking
python -m pip install .
```

To install development dependencies as well:

```bash
python -m pip install .[dev]
```

## Running

`pyproject.toml` defines a CLI command:

```bash
pha version
pha scan .
```

If the entry point is not available, you can run the module directly:

```bash
python -m project_health.cli version
python -m project_health.cli scan .
```

## Command Examples

Print the current version:

```bash
pha version
```

Scan the current project with terminal output:

```bash
pha scan .
```

Scan another directory:

```bash
pha scan /path/to/project
```

Generate a JSON report:

```bash
pha scan . --output-format json
```

Use the short format option:

```bash
pha scan . -o terminal
pha scan . -o json
```

## Program Output

After `scan` runs, the program:

1. collects the results of individual checks;
2. calculates the final average `score`;
3. assigns a status:
   - `Critical` for scores below `40`;
   - `Weak` for scores from `40` to `69`;
   - `Good` for scores from `70` to `89`;
   - `Excellent` for scores from `90`.

The terminal report includes:

- a compact header panel with the project path, detected stack, final score, score bar, and status;
- a `Tools` section with required and available tools;
- dependency lines for runtime and development packages when they are detected;
- a compact `Dependencies: none detected` line when no dependency lists are available;
- a `Status` section with a short explanation of the final status;
- a `Checks` table with `Check`, `Result`, `Score`, and `Issues`;
- a numbered `Recommendations` list, or `No recommendations` when there are none.

The JSON output still uses the same `--output-format json` or `-o json` flag and returns a serialized report object containing at least:

- `path`;
- `score`;
- `status`;
- `checks`;
- `recommendations`;
- `detected_stack`;
- `required_tools`;
- `available_tools`.

## Development

The project has three main layers:

- `scanners` collect facts about the project and its environment;
- `analyzers` convert those facts into a final report and recommendation list;
- `reports` handle output formatting.

The CLI entry point is located in `project_health/cli.py`. The `scan` command does the following:

1. runs `ProjectScanner`;
2. passes the result to `ReadinessAnalyzer`;
3. renders the report through `TerminalReport` or `JsonReport`.

## Running Tests

The project includes `pytest` tests.

Install test dependencies:

```bash
python -m pip install .[dev]
```

Run all tests:

```bash
pytest
```

You can also run specific test files, for example:

```bash
pytest tests/test_cli.py
pytest tests/test_project_scanner.py
```

## Common Errors and Fixes

`Path does not exist: ...`
Check the path passed to `pha scan`.

`output_format must be 'terminal' or 'json'.`
Use only `terminal` or `json`.

`pha scan <path> --json` does not work
The CLI does not implement a `--json` flag. Use `pha scan <path> --output-format json` or `pha scan <path> -o json`.

`python not found`, `pip not found`, `docker not found`, and similar messages
Install the missing tool or adjust the project configuration so the tool is not required unnecessarily.

`python version mismatch: required ..., found ...`
The current Python version does not match the requirement from `.python-version` or dependency files. Use a matching version via `.venv`, `pyenv`, or the system Python.

`No dependency or build files found`
The scanned project does not contain any known dependency or build files. Add `pyproject.toml`, `requirements.txt`, `Pipfile`, or another supported file.

`README file not found` / `License file not found`
Add a `README` file and a license file to the repository root.

## Project Status

The project is currently at version `0.1.0`. It already includes a working CLI, a set of scanners, two report formats, and automated tests, but based on the current version and structure it should still be treated as an early-stage project rather than a mature public release.
