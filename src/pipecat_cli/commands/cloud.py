#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Cloud command implementation for Pipecat Cloud integration.

This module wraps the pipecatcloud CLI to make it available as a subcommand.
Both `pcc` and `pipecat cloud` use the exact same underlying implementation
from the pipecatcloud library, ensuring consistency.
"""

import sys

import typer

# Create a thin wrapper that calls the pipecatcloud CLI
cloud_app = typer.Typer(
    name="cloud",
    help="Deploy and manage bots on Pipecat Cloud",
    add_completion=False,
    invoke_without_command=True,
)


@cloud_app.callback()
def cloud_callback(ctx: typer.Context):
    """
    Pipecat Cloud - Deploy and manage production bots.

    This command delegates to the pipecatcloud CLI (pcc), ensuring both
    tools use the same implementation.
    """
    # Import the actual pcc entrypoint
    from pipecatcloud.__main__ import main as pcc_main

    # If no subcommand was provided, let pcc handle it (will show help)
    if not ctx.invoked_subcommand:
        # Remove 'cloud' from argv so pcc sees the right arguments
        # e.g., "pipecat cloud --help" -> "pcc --help"
        original_argv = sys.argv.copy()
        try:
            # Find and remove 'cloud' from argv
            if "cloud" in sys.argv:
                cloud_idx = sys.argv.index("cloud")
                sys.argv = sys.argv[:cloud_idx] + sys.argv[cloud_idx + 1 :]
            pcc_main()
        finally:
            sys.argv = original_argv
        raise typer.Exit()


# For any subcommand (auth, deploy, etc.), delegate to pcc
@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def auth(ctx: typer.Context):
    """Manage Pipecat Cloud credentials."""
    _delegate_to_pcc("auth", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def deploy(ctx: typer.Context):
    """Deploy an agent to Pipecat Cloud."""
    _delegate_to_pcc("deploy", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def agent(ctx: typer.Context):
    """Manage deployed agents."""
    _delegate_to_pcc("agent", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def docker(ctx: typer.Context):
    """Docker build and push utilities."""
    _delegate_to_pcc("docker", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def run(ctx: typer.Context):
    """Run an agent locally."""
    _delegate_to_pcc("run", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def secrets(ctx: typer.Context):
    """Manage secrets and image pull secrets."""
    _delegate_to_pcc("secrets", ctx)


@cloud_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def organizations(ctx: typer.Context):
    """Manage organizations."""
    _delegate_to_pcc("organizations", ctx)


def _delegate_to_pcc(command: str, ctx: typer.Context):
    """
    Delegate to the pcc command by manipulating sys.argv and calling pcc's main.

    Args:
        command: The pcc command to run (e.g., "auth", "deploy")
        ctx: Typer context containing extra arguments
    """
    from pipecatcloud.__main__ import main as pcc_main

    # Save original argv
    original_argv = sys.argv.copy()

    try:
        # Reconstruct argv for pcc: ["pcc", command, ...extra_args]
        # e.g., "pipecat cloud auth login" -> "pcc auth login"
        sys.argv = ["pcc", command] + list(ctx.args)
        pcc_main()
    finally:
        # Restore original argv
        sys.argv = original_argv
