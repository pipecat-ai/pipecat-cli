#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Init command implementation for creating new Pipecat projects."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from pipecat_cli.generators import ProjectGenerator
from pipecat_cli.prompts import ask_project_questions

console = Console()


def init_command(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory (defaults to current directory)"
    ),
):
    """
    Initialize a new Pipecat project.

    Creates a complete project structure with bot.py, dependencies, and configuration files
    based on your selections. Uses an interactive wizard to guide you through the setup.

    Example:
        pc init                   # Create in current directory
        pc init -o ./my-bot       # Create in specified directory
    """
    try:
        # Interactive mode: ask questions
        config = ask_project_questions()

        # Generate project
        generator = ProjectGenerator(config)
        project_path = generator.generate(output_dir)

        # Show next steps
        generator.print_next_steps(project_path)

    except KeyboardInterrupt:
        console.print("\n[yellow]Project creation cancelled.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Error creating project: {e}[/red]")
        raise typer.Exit(1)
