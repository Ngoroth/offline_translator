#!/bin/bash
set -e

echo "Running Ruff Lint..."
uv run ruff check .

echo "Running Type Check (basedpyright)..."
uv run basedpyright

echo "Running Tests..."
uv run pytest

echo "ALL CHECKS PASSED"
