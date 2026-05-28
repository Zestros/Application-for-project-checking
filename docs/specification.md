# Specification

## Purpose

Project Health helps students, teachers, beginner developers, and small teams quickly evaluate whether a Python project contains the minimum artifacts expected from a reproducible engineering project.

The tool does not replace linters, test runners, or CI systems. Its responsibility is to inspect project readiness at the repository level and explain what is missing.

## Users

- Student or beginner developer preparing a project for submission.
- Teacher or reviewer checking whether a submitted project is reproducible.
- Maintainer checking a repository before publishing or continuing development.

## Main Scenarios

### Scan Current Project

A user runs `pha scan .`.

The tool scans the current directory, calculates a readiness score, and prints a terminal report with checks and recommendations.

### Scan Another Project

A user runs `pha scan path/to/project`.

The tool scans the selected directory instead of the current one. If the path does not exist, the command fails with a clear validation error.

### Generate JSON Report

A user runs `pha scan . --output-format json`.

The tool returns a serialized report that can be consumed by another script or automated check.

### Inspect Missing Environment Tools

When dependency files indicate that Python, pip, Docker, Poetry, Pipenv, or another supported tool is required, Project Health checks whether the tool is available locally and includes the result in the report.

## Functional Requirements

- The CLI must provide a `scan` command.
- The CLI must provide a `version` command.
- The scan command must accept a target path.
- The scan command must support terminal and JSON output formats.
- The scan command must reject missing paths.
- The scan command must reject unsupported output formats.
- The scanner must check for README files.
- The scanner must check for license files.
- The scanner must check for Git metadata and `.gitignore`.
- The scanner must detect common Python dependency and build files.
- The scanner must detect required local tools from project configuration.
- The analyzer must calculate a numeric score.
- The analyzer must assign a readiness status.
- The analyzer must produce recommendations for failed or weak checks.
- The report layer must render the same report data in terminal and JSON formats.

## Error Cases

- Missing target path: the CLI returns a validation error.
- Unsupported output format: the CLI returns a validation error.
- Missing README: the report contains a failed or weak README check.
- Missing license: the report contains a failed license check.
- Missing dependency files: the report recommends adding a supported dependency or build file.
- Missing required tools: the report lists unavailable tools and recommends installing them.

## Non-Goals

- Project Health does not run the target project's tests.
- Project Health does not perform static code analysis.
- Project Health does not deploy applications.
- Project Health does not guarantee that a project is production-ready.

