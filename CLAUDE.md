# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pipecat CLI (`pipecat` / `pc`) is a code generation and scaffolding tool for building, deploying, and monitoring Pipecat AI voice agents. The main command is `pipecat init`, which generates complete project skeletons from Jinja2 templates. It supports both interactive (Questionary prompts) and non-interactive (CLI flags / JSON config) modes.

## Common Commands

```bash
uv sync --all-extras --dev          # Install all dependencies
uv run pytest                       # Run all tests
uv run pytest tests/test_service_registry.py  # Run a single test file
uv run pytest -k "test_name"        # Run a specific test
uv run pytest -m "not slow"         # Skip slow tests
uv run ruff check src/              # Lint
uv run ruff format src/             # Format
uv run scripts/update_registry.py   # Regenerate _imports.py and _configs.py
uv run scripts/check_registry.py    # Validate registry completeness
```

## Architecture

### CLI Framework
- **Typer** app in `src/pipecat_cli/main.py` — registers the `init` command directly, then discovers external commands (`cloud`, `tail`) via the `pipecat_cli.extensions` entry point group.
- Entry points: both `pipecat` and `pc` map to `pipecat_cli.main:app`.

### Service Registry (src/pipecat_cli/registry/)
Three-layer pattern with strict ownership:

1. **`service_metadata.py`** — **SOURCE OF TRUTH**. All `ServiceDefinition` entries for transports, STT, LLM, TTS, realtime, and video services live here. Also contains `FEATURE_DEFINITIONS` and `MANUAL_SERVICE_CONFIGS`. Edit this file when adding/changing services.
2. **`service_loader.py`** — Query and validation logic. Static methods for finding services, getting imports, resolving extras. All operations on registry data go here.
3. **`_configs.py` / `_imports.py`** — **AUTO-GENERATED. Never edit directly.** Regenerate with `uv run scripts/update_registry.py` after changing `service_metadata.py`.

### Adding a New Service
1. Add a `ServiceDefinition` to the appropriate list in `service_metadata.py`
2. Run `uv run scripts/update_registry.py`
3. Run tests to verify: `uv run pytest tests/test_service_registry.py`

### Project Generation (src/pipecat_cli/generators/)
- `project.py` orchestrates file creation using Jinja2 templates from `src/pipecat_cli/templates/`.
- Templates are organized: `server/` (bot.py, server.py, pyproject.toml, etc.), `client/` (vanilla-js-vite, react-vite, react-nextjs), `_readme_blocks/`.
- Generated Python files are auto-formatted with Ruff post-generation.

### Interactive vs Non-Interactive
- **Interactive**: `questions.py` drives a Questionary-based prompt flow, producing a `ProjectConfig` dataclass.
- **Non-interactive**: Triggered by `--name` or `--config` flags. `config_validator.py` handles validation, collecting **all** errors before raising (not fail-fast). Supports `--dry-run` to output resolved config as JSON.

## Code Style

- Ruff with line-length 100. Only import sorting rules (`select = ["I"]`).
- Pre-commit hooks: `ruff --fix` and `ruff-format`.
- Tests are excluded from Ruff linting.
