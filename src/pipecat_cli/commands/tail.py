#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Tail command implementation for Pipecat observability."""

import asyncio

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
        pipecat tail                              # Connect to local bot
        pipecat tail --url wss://bot.example.com  # Connect to remote bot
    """
    # Lazy import - only load pipecat-ai-tail when tail command is actually used
    # This allows the init command to run faster and removes Pipecat log lines
    # from printing while using the init command.
    from pipecat_tail.cli import PipecatTail

    # Create and run the tail dashboard using the Python API
    app = PipecatTail(url=url)
    asyncio.run(app.run())
