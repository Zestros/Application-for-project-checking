.PHONY: help venv install test coverage build run docker-build docker-run

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
	@echo "build         build package distributions"
	@echo "run           run CLI scan for SCAN_PATH, default current directory"
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

build:
	$(VENV_PYTHON) -m build --no-isolation

run:
	$(VENV_PHA) scan $(SCAN_PATH)

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) scan /workspace
