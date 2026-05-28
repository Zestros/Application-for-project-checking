.PHONY: help venv install test coverage coverage-html build run docs docker-build docker-run

IMAGE_NAME ?= project-health
SCAN_PATH ?= .
PYTHON ?= python
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PHA := $(VENV)/bin/pha

help:
	@echo "venv          create local virtual environment"
	@echo "install       install package with development dependencies"
	@echo "test          run tests"
	@echo "coverage      run tests with coverage report"
	@echo "coverage-html run tests with HTML coverage report"
	@echo "build         build package distributions"
	@echo "run           run CLI scan for SCAN_PATH, default current directory"
	@echo "docs          build project documentation"
	@echo "docker-build  build Docker image"
	@echo "docker-run    run CLI scan inside Docker for the current repository"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

test:
	$(VENV_PYTHON) -m pytest

coverage:
	$(VENV_PYTHON) -m pytest --cov=project_health --cov-report=term-missing

coverage-html:
	$(VENV_PYTHON) -m pytest --cov=project_health --cov-report=term-missing --cov-report=html

build:
	$(VENV_PYTHON) -m build --no-isolation

run:
	$(VENV_PHA) scan $(SCAN_PATH)

docs:
	$(VENV_PYTHON) -m mkdocs build

docs-serve:
	$(VENV_PYTHON) -m mkdocs serve

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) scan /workspace
