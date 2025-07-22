#!/bin/bash
set -e

# Create a virtual environment and upgrade pip/setuptools/wheel
python3 -m venv --upgrade-deps .venv
. .venv/bin/activate

# uv is already available (installed via Dockerfile). Use uv to install:
# 1) the project in editable mode
# 2) all dev dependencies (from pyproject.toml [project.optional-dependencies])
uv pip install --editable . --group dev


# Set up pre-commit hooks
pre-commit install
