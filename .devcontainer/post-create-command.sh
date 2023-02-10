#!/bin/bash
set -e

# Add user's fork as a remote
GIT_USER=$(git config user.name)
if [ ! git remote | grep -q "fork" ]; then
    git remote add fork https://github.com/${GIT_USER}/flask
fi

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools

# Install the development dependencies, then install Flask in editable mode
pip install -r requirements/dev.txt && pip install -e .

# Install pre-commit hooks and coverage
pre-commit install
pip install coverage
