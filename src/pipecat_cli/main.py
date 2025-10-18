#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Main CLI entry point for Pipecat CLI."""

from importlib.metadata import version

import typer
from rich.console import Console

from pipecat_cli.commands import init, tail
from pipecat_cli.commands.cloud import cloud_app

app = typer.Typer(
    name="pipecat",
    help="CLI tool for scaffolding Pipecat AI voice agent projects",
    add_completion=False,
)

console = Console()

# Register commands
# Single-level commands use app.command() decorator
app.command(name="init", help="Initialize a new Pipecat project")(init.init_command)
app.command(name="tail", help="Monitor Pipecat sessions in real-time")(tail.tail_command)

# Multi-level command groups use app.add_typer() to register sub-applications
# This allows commands like: pipecat cloud auth, pipecat cloud deploy, etc.
app.add_typer(cloud_app, name="cloud")


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        try:
            pkg_version = version("pipecat-ai-cli")
        except Exception:
            pkg_version = "unknown"
        console.print(f"ᓚᘏᗢ Pipecat CLI Version: [green]{pkg_version}[/green]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Pipecat CLI - Build AI voice agents with ease."""
    if ctx.invoked_subcommand is None:
        console.print("\n[bold cyan]🎙️  Pipecat CLI[/bold cyan]")
        console.print("\nScaffold AI voice agent projects with minimal boilerplate.\n")
        console.print("Available commands:")
        console.print("  [bold]pipecat init[/bold]   - Initialize a new Pipecat project")
        console.print("  [bold]pipecat tail[/bold]   - Monitor bots in real-time")
        console.print("  [bold]pipecat cloud[/bold]  - Deploy and manage bots on Pipecat Cloud")
        console.print("\nRun [bold]pipecat --help[/bold] for more information.\n")


if __name__ == "__main__":
    app()
