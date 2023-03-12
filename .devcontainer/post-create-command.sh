#!/bin/bash
set -e

# Add user's fork as a remote
# if ! git remote | grep -q "fork"; then
#     git remote add fork https://github.com/${GITHUB_USER}/flask
# fi

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements/dev.txt && pip install -e .
pre-commit install
