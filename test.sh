#!/usr/bin/env bash
set -e

MODE=$1

if [ "$MODE" = "base" ]; then
    echo "Running base (existing) tests..."
    pytest
elif [ "$MODE" = "new" ]; then
    echo "Running new tests only..."
    pytest tests/test_views.py
else
    echo "Usage:"
    echo "  ./test.sh base   # run existing tests"
    echo "  ./test.sh new    # run new tests only"
    exit 1
fi
