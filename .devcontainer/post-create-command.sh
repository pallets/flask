#!/bin/bash
set -e

# Add user's fork as a remote
if ! git remote | grep -q "fork"; then
    git remote add fork https://github.com/${GITHUB_USER}/flask
fi

# Create and activate a virtualenv
python3 -m venv .venv
. .venv/bin/activate

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools

# Install the development dependencies, then install Flask in editable mode
pip install -r requirements/dev.txt && pip install -e .

# Install pre-commit hooks and coverage
pre-commit install
pip install coverage
