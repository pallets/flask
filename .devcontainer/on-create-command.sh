#!/bin/bash
set -e

if ! git remote | grep -q "fork"; then
    git remote add fork https://github.com/${GITHUB_USER}/flask
fi

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements/dev.txt && pip install -e .
pre-commit install

sudo cp .devcontainer/welcome-message.txt /usr/local/etc/vscode-dev-containers/first-run-notice.txt
