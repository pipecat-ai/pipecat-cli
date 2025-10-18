#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Running ruff format (using pyproject.toml config)..."
ruff format .

echo "Running ruff check with auto-fix (using pyproject.toml config)..."
ruff check --fix .

echo "✅ Done! All auto-fixable issues have been resolved."

