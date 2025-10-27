#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Test command for running frame processor unit tests."""

import asyncio
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def test_command(
    processor_file: Path = typer.Argument(
        ...,
        help="Python file containing the processor to test",
        exists=True,
    ),
    frames: Optional[Path] = typer.Option(
        None,
        "--frames",
        "-f",
        help="JSON file containing test frames",
        exists=True,
    ),
    processor_class: Optional[str] = typer.Option(
        None,
        "--processor",
        "-p",
        help="Processor class name (auto-detected if not provided)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
):
    """
    Test a custom frame processor.

    Loads a processor from a Python file and runs it with test frames from a JSON file.
    If no expected output is specified in the JSON, the command will display the actual
    output for exploratory testing.

    Example:
        pipecat test my_processor.py --frames test_frames.json
        pipecat test my_processor.py -f test.json -p MyProcessor

    JSON Format:
        {
          "input_frames": [
            {"type": "TextFrame", "text": "hello"}
          ],
          "expected_output": [
            {"type": "TextFrame", "text": "HELLO"},
            {"type": "EndFrame"}
          ]
        }
    """
    try:
        # Import the processor module
        processor_instance = _load_processor(processor_file, processor_class)

        if frames is None:
            console.print("[red]Error: --frames/-f is required[/red]")
            raise typer.Exit(1)

        # Run the test
        asyncio.run(_run_test(processor_instance, frames, verbose))

    except KeyboardInterrupt:
        console.print("\n[yellow]Test cancelled.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def _load_processor(processor_file: Path, processor_class: Optional[str]):
    """Load a processor class from a Python file."""
    try:
        # Add the processor file's directory to sys.path
        processor_dir = processor_file.parent.absolute()
        if str(processor_dir) not in sys.path:
            sys.path.insert(0, str(processor_dir))

        # Import the module
        spec = importlib.util.spec_from_file_location("test_module", processor_file)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load module from {processor_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Import FrameProcessor for type checking
        from pipecat.processors.frame_processor import FrameProcessor

        # Find processor class
        if processor_class:
            # Use specified class name
            if not hasattr(module, processor_class):
                raise ValueError(f"Class '{processor_class}' not found in {processor_file}")
            cls = getattr(module, processor_class)
        else:
            # Auto-detect: find first FrameProcessor subclass
            processor_classes = []
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, FrameProcessor)
                    and obj != FrameProcessor
                    and obj.__module__ == module.__name__
                ):
                    processor_classes.append((name, obj))

            if not processor_classes:
                raise ValueError(
                    f"No FrameProcessor subclass found in {processor_file}. "
                    "Use --processor to specify the class name."
                )

            if len(processor_classes) > 1:
                names = [name for name, _ in processor_classes]
                raise ValueError(
                    f"Multiple FrameProcessor classes found: {', '.join(names)}. "
                    "Use --processor to specify which one to test."
                )

            _, cls = processor_classes[0]

        # Instantiate the processor
        try:
            return cls()
        except TypeError as e:
            raise ValueError(
                f"Could not instantiate {cls.__name__}. "
                f"Make sure it has a no-argument constructor or provide default arguments. "
                f"Error: {e}"
            )

    except Exception as e:
        raise ValueError(f"Failed to load processor: {e}")


async def _run_test(processor, frames_file: Path, verbose: bool):
    """Run the test and display results."""
    from pipecat.tests import run_test_from_file, frame_to_dict

    console.print(f"\n[bold cyan]Testing {processor.__class__.__name__}[/bold cyan]")
    console.print(f"Frames: {frames_file}\n")

    # Run the test
    with console.status("[bold green]Running test..."):
        output_frames, expected_output, passed = await run_test_from_file(
            processor, str(frames_file)
        )

    # Display results
    if expected_output is None:
        # Exploratory mode: just show output
        _display_exploratory_output(output_frames, verbose)
    else:
        # Validation mode: show pass/fail
        _display_validation_results(output_frames, expected_output, passed, verbose)


def _display_exploratory_output(output_frames, verbose: bool):
    """Display output frames in exploratory mode."""
    console.print("[bold yellow]Exploratory Mode[/bold yellow] (no expected output specified)\n")

    if not output_frames:
        console.print("[dim]No frames output[/dim]")
        return

    console.print(f"[bold]Output Frames ({len(output_frames)}):[/bold]\n")

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", style="cyan")

    if verbose:
        table.add_column("Data", style="white")

    from pipecat.tests import frame_to_dict

    for i, frame in enumerate(output_frames, 1):
        frame_dict = frame_to_dict(frame)
        frame_type = frame_dict["type"]

        if verbose:
            # Show all fields except type
            data_fields = {k: v for k, v in frame_dict.items() if k != "type"}
            data_str = json.dumps(data_fields, indent=2) if data_fields else "{}"
            table.add_row(str(i), frame_type, data_str)
        else:
            table.add_row(str(i), frame_type)

    console.print(table)

    # Show JSON output for easy copy-paste
    console.print("\n[bold]Copy this to create expected_output:[/bold]")
    from pipecat.tests import frame_to_dict

    expected = [frame_to_dict(f) for f in output_frames]
    json_output = json.dumps(expected, indent=2)
    syntax = Syntax(json_output, "json", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, border_style="green"))


def _display_validation_results(output_frames, expected_output, passed: bool, verbose: bool):
    """Display validation results."""
    if passed:
        console.print("[bold green]✓ Test Passed[/bold green]\n")
    else:
        console.print("[bold red]✗ Test Failed[/bold red]\n")

    # Show comparison
    console.print(f"[bold]Expected: {len(expected_output)} frames[/bold]")
    console.print(f"[bold]Actual: {len(output_frames)} frames[/bold]\n")

    if not passed or verbose:
        # Show detailed comparison
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Expected", style="cyan")
        table.add_column("Actual", style="yellow")
        table.add_column("Match", style="white")

        from pipecat.tests import frame_to_dict

        max_len = max(len(expected_output), len(output_frames))
        for i in range(max_len):
            idx = str(i + 1)

            if i < len(expected_output):
                expected = expected_output[i]
                expected_str = expected.get("type", "???")
            else:
                expected_str = "[dim]—[/dim]"

            if i < len(output_frames):
                actual = frame_to_dict(output_frames[i])
                actual_str = actual.get("type", "???")
            else:
                actual_str = "[dim]—[/dim]"

            # Check if they match
            if i < len(expected_output) and i < len(output_frames):
                match = "✓" if actual_str == expected_str else "✗"
                match_style = "green" if match == "✓" else "red"
                match_str = f"[{match_style}]{match}[/{match_style}]"
            else:
                match_str = "[red]✗[/red]"

            table.add_row(idx, expected_str, actual_str, match_str)

        console.print(table)

    # Exit with appropriate code
    if not passed:
        raise typer.Exit(1)
