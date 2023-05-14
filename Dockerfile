FROM python:3.10

WORKDIR /app

COPY . .

RUN python3 -m venv venv

RUN python3 -m pip install .

# Run basic test suite
RUN python3 -m pip install pytest
RUN pytest

# Run entire test suite
RUN python3 -m pip install tox
RUN tox
