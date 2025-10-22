#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Cloud command implementation for Pipecat Cloud integration.

This module integrates the pipecatcloud CLI as a subcommand using the Python API.
Both `pcc` and `pipecat cloud` use the exact same underlying Typer app
from the pipecatcloud library, ensuring consistency.
"""

import typer


# Lazy import - only load pipecatcloud when cloud command is actually used
# This allows other commands to run without loading cloud dependencies
def _get_cloud_app() -> typer.Typer:
    """Get the pipecatcloud Typer app."""
    from pipecatcloud.cli.entry_point import entrypoint_cli_typer

    return entrypoint_cli_typer


# Export the cloud app directly
# This uses the pipecatcloud CLI's Typer app, so all commands
# (auth, deploy, agent, docker, run, secrets, organizations) are automatically
# available without any wrapping or sys.argv manipulation.
cloud_app = _get_cloud_app()
