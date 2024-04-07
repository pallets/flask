#!/bin/bash
set -e
python3 -m venv --upgrade-deps .venv
. .venv/bin/activate
pip install -r requirements/dev.txt
pip install -e .
pre-commit install --install-hooks
