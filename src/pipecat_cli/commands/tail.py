#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Tail command implementation for Pipecat observability."""

import sys

import typer
from rich.console import Console

console = Console()


def tail_command(
    url: str = typer.Option(
        "ws://localhost:9292",
        "--url",
        "-u",
        help="WebSocket URL to connect to",
    ),
):
    """
    Monitor Pipecat sessions in real-time.

    Pipecat Tail provides real-time observability and debugging for your bots:
    - System logs
    - Live conversation tracking
    - Audio level monitoring
    - Service metrics and usage stats

    Example:
        pipecat tail                          # Connect to local bot
        pipecat tail -u wss://bot.example.com # Connect to remote bot
    """
    # Lazy import - only load pipecat-ai-tail when tail command is actually used
    # This allows the init command to run faster and removes Pipecat log lines
    # from printing while using the init command.
    from pipecat_tail.cli import main as tail_main

    # Set up sys.argv for tail's argument parser
    sys.argv = ["pipecat-tail", "-u", url]
    tail_main()
