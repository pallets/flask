#!/bin/bash
set -e

# Add user's fork as a remote
GIT_USER=$(git config user.name)
git remote add fork https://github.com/${GIT_USER}/flask

# Create and activate a virtualenv
python3 -m venv .venv
. .venv/bin/activate

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools
echo "Upgraded setuptools"

# Install the development dependencies, then install Flask in editable mode
pip install -r requirements/dev.txt && pip install -e .
echo "Installed dependencies and Flask"

# Install pre-commit hooks
pre-commit install
echo "Installed pre-commit hooks"

# Install coverage
pip install coverage
echo "Installed coverage"
