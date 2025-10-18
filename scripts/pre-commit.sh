#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Running pre-commit checks..."

# Change to project root (one level up from scripts/)
cd "$(dirname "$0")/.."

# Format check for Python
echo "📝 Checking Python code formatting..."
if ! NO_COLOR=1 ruff format --diff --check; then
    echo -e "${RED}❌ Python formatting issues found. Run 'ruff format' to fix.${NC}"
    exit 1
fi

# Lint check for Python
echo "🔍 Running Python linter..."
if ! ruff check; then
    echo -e "${RED}❌ Python linting issues found.${NC}"
    exit 1
fi

# Format check for Jinja2 templates
echo "📝 Checking Jinja2 template formatting..."
if ! djlint src/pipecat_cli/templates/ --check; then
    echo -e "${YELLOW}⚠️  Jinja2 formatting issues found. Run 'djlint src/pipecat_cli/templates/ --reformat' to fix.${NC}"
    # Don't exit on djlint formatting issues, just warn
fi

# Lint check for Jinja2 templates
echo "🔍 Running Jinja2 template linter..."
if ! djlint src/pipecat_cli/templates/ --lint; then
    echo -e "${YELLOW}⚠️  Jinja2 linting issues found. Review and fix manually.${NC}"
    # Don't exit on djlint issues, just warn (templates may have intentional deviations)
fi

echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"

