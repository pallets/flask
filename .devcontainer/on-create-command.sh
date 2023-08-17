#!/bin/bash
set -e

python3 -m venv .venv
. .venv/bin/activate
pip3 install -U pip
pip3 install -r requirements/dev.txt
pip3 install -e .
pre-commit install --install-hooks
