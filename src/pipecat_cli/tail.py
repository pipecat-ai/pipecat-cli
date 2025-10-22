#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Pipecat Tail - Real-time observability for Pipecat bots.

This module re-exports the main classes from pipecat-ai-tail for convenience.
Users can import these directly from pipecat_cli.tail instead of pipecat_tail.

Example:
    from pipecat_cli.tail import TailObserver, TailRunner

    # Option 1: Use TailRunner as a drop-in replacement for PipelineRunner
    runner = TailRunner()
    await runner.run(task)

    # Option 2: Add TailObserver to your pipeline task
    task = PipelineTask(..., observers=[TailObserver()])
"""

# Re-export main classes from pipecat-ai-tail
from pipecat_tail.observer import TailObserver
from pipecat_tail.runner import TailRunner

__all__ = ["TailObserver", "TailRunner"]
