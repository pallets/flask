# Base image: Match with .readthedocs.yaml and pyproject.toml
FROM mcr.microsoft.com/devcontainers/python:3.13

# Install uv and pre-commit globally
RUN pip install --upgrade pip setuptools wheel uv pre-commit

# Set workdir and default shell
WORKDIR /workspaces/flask
SHELL ["/bin/bash", "-c"]
