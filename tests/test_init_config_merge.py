#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Tests for CLI flag vs --config file precedence in `pc init`."""

import json

from typer.testing import CliRunner

from pipecat_cli.main import app

runner = CliRunner()

BASE_CONFIG = {
    "name": "merge-bot",
    "bot_type": "web",
    "transports": ["daily"],
    "mode": "cascade",
    "stt": "deepgram_stt",
    "llm": "openai_llm",
    "tts": "cartesia_tts",
}


def _write_config(tmp_path, **overrides):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({**BASE_CONFIG, **overrides}), encoding="utf-8")
    return config_file


def test_config_file_enables_evals(tmp_path):
    """An "evals": true config key scaffolds evals when the flag is omitted."""
    config_file = _write_config(tmp_path, evals=True)
    result = runner.invoke(app, ["init", "--config", str(config_file), "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output

    assert (tmp_path / "merge-bot" / "server" / "evals" / "scenario.yaml").exists()


def test_no_evals_flag_overrides_config_file(tmp_path):
    """An explicit --no-evals beats "evals": true in the config file."""
    config_file = _write_config(tmp_path, evals=True)
    result = runner.invoke(
        app, ["init", "--config", str(config_file), "--no-evals", "-o", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output

    project = tmp_path / "merge-bot"
    assert (project / "server" / "bot.py").exists()
    assert not (project / "server" / "evals").exists()
    assert '"eval": lambda' not in (project / "server" / "bot.py").read_text(encoding="utf-8")


def test_evals_flag_overrides_config_file(tmp_path):
    """An explicit --evals beats an "evals": false config value."""
    config_file = _write_config(tmp_path, evals=False)
    result = runner.invoke(
        app, ["init", "--config", str(config_file), "--evals", "-o", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output

    assert (tmp_path / "merge-bot" / "server" / "evals" / "scenario.yaml").exists()


def test_evals_defaults_off_without_flag_or_config_key(tmp_path):
    """With no flag and no config key, evals are not scaffolded non-interactively."""
    config_file = _write_config(tmp_path)
    result = runner.invoke(app, ["init", "--config", str(config_file), "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output

    assert not (tmp_path / "merge-bot" / "server" / "evals").exists()
