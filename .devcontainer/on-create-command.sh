#!/bin/bash
set -e

python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements/dev.txt
pip install -e .
pre-commit install --install-hooks
