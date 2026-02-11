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
    # --- Non-interactive flags ---
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Project name (triggers non-interactive mode)"
    ),
    bot_type: Optional[str] = typer.Option(
        None, "--bot-type", "-b", help="Bot type: 'web' or 'telephony'"
    ),
    transport: Optional[list[str]] = typer.Option(
        None, "--transport", "-t", help="Transport (repeatable, e.g. -t daily -t smallwebrtc)"
    ),
    mode: Optional[str] = typer.Option(
        None, "--mode", "-m", help="Pipeline mode: 'cascade' or 'realtime'"
    ),
    stt: Optional[str] = typer.Option(None, "--stt", help="STT service (cascade mode)"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM service (cascade mode)"),
    tts: Optional[str] = typer.Option(None, "--tts", help="TTS service (cascade mode)"),
    realtime: Optional[str] = typer.Option(
        None, "--realtime", help="Realtime service (realtime mode)"
    ),
    video: Optional[str] = typer.Option(None, "--video", help="Video avatar service"),
    client_framework: Optional[str] = typer.Option(
        None, "--client-framework", help="Client framework: 'react', 'vanilla', or 'none'"
    ),
    client_server: Optional[str] = typer.Option(
        None, "--client-server", help="Client dev server: 'vite' or 'nextjs'"
    ),
    daily_pstn_mode: Optional[str] = typer.Option(
        None, "--daily-pstn-mode", help="Daily PSTN mode: 'dial-in' or 'dial-out'"
    ),
    twilio_daily_sip_mode: Optional[str] = typer.Option(
        None, "--twilio-daily-sip-mode", help="Twilio+Daily SIP mode: 'dial-in' or 'dial-out'"
    ),
    recording: bool = typer.Option(False, "--recording/--no-recording", help="Enable recording"),
    transcription: bool = typer.Option(
        False, "--transcription/--no-transcription", help="Enable transcription"
    ),
    smart_turn: Optional[bool] = typer.Option(
        None, "--smart-turn/--no-smart-turn", help="Enable smart turn-taking (default: True for cascade)"
    ),
    video_input: bool = typer.Option(
        False, "--video-input/--no-video-input", help="Enable video input"
    ),
    video_output: bool = typer.Option(
        False, "--video-output/--no-video-output", help="Enable video output"
    ),
    deploy_to_cloud: bool = typer.Option(
        True, "--deploy-to-cloud/--no-deploy-to-cloud", help="Generate cloud deployment files"
    ),
    enable_krisp: bool = typer.Option(
        False, "--enable-krisp/--no-enable-krisp", help="Enable Krisp noise cancellation"
    ),
    observability: bool = typer.Option(
        False, "--observability/--no-observability", help="Enable observability"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="JSON config file (triggers non-interactive mode)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print resolved config as JSON without generating files"
    ),
):
    """
    Initialize a new Pipecat project.

    Creates a complete project structure with bot.py, dependencies, and configuration files.

    In interactive mode (default), uses a wizard to guide you through setup.
    In non-interactive mode (when --name or --config is provided), all configuration
    is taken from flags or a config file.

    Examples:
        pc init                                          # Interactive wizard
        pc init --name my-bot --bot-type web \\
          --transport daily --mode cascade \\
          --stt deepgram_stt --llm openai_llm \\
          --tts cartesia_tts                             # Non-interactive
        pc init --config project-config.json             # From config file
        pc init --name my-bot ... --dry-run              # Preview config as JSON
    """
    try:
        non_interactive = name is not None or config is not None

        if non_interactive:
            from pipecat_cli.config_validator import (
                ConfigValidationError,
                config_to_json,
                load_config_from_file,
                validate_and_build_config,
            )

            # Load from config file if provided
            if config is not None:
                file_data = load_config_from_file(config)
                # CLI flags override file values
                name = name or file_data.get("name") or file_data.get("project_name")
                bot_type = bot_type or file_data.get("bot_type")
                transport = transport or file_data.get("transports") or file_data.get("transport")
                mode = mode or file_data.get("mode")
                stt = stt or file_data.get("stt") or file_data.get("stt_service")
                llm = llm or file_data.get("llm") or file_data.get("llm_service")
                tts = tts or file_data.get("tts") or file_data.get("tts_service")
                realtime = realtime or file_data.get("realtime") or file_data.get("realtime_service")
                video = video or file_data.get("video") or file_data.get("video_service")
                client_framework = client_framework or file_data.get("client_framework")
                client_server = client_server or file_data.get("client_server")
                daily_pstn_mode = daily_pstn_mode or file_data.get("daily_pstn_mode")
                twilio_daily_sip_mode = (
                    twilio_daily_sip_mode or file_data.get("twilio_daily_sip_mode")
                )
                recording = recording or file_data.get("recording", False)
                transcription = transcription or file_data.get("transcription", False)
                if smart_turn is None:
                    smart_turn = file_data.get("smart_turn")
                video_input = video_input or file_data.get("video_input", False)
                video_output = video_output or file_data.get("video_output", False)
                if "deploy_to_cloud" in file_data:
                    deploy_to_cloud = file_data["deploy_to_cloud"]
                enable_krisp = enable_krisp or file_data.get("enable_krisp", False)
                observability = observability or file_data.get(
                    "observability", file_data.get("enable_observability", False)
                )

            try:
                project_config = validate_and_build_config(
                    name=name,
                    bot_type=bot_type,
                    transport=transport,
                    mode=mode,
                    stt=stt,
                    llm=llm,
                    tts=tts,
                    realtime=realtime,
                    video=video,
                    client_framework=client_framework,
                    client_server=client_server,
                    daily_pstn_mode=daily_pstn_mode,
                    twilio_daily_sip_mode=twilio_daily_sip_mode,
                    recording=recording,
                    transcription=transcription,
                    smart_turn=smart_turn,
                    video_input=video_input,
                    video_output=video_output,
                    deploy_to_cloud=deploy_to_cloud,
                    enable_krisp=enable_krisp,
                    observability=observability,
                )
            except ConfigValidationError as e:
                console.print(f"\n[red]{e}[/red]")
                raise typer.Exit(1)

            if dry_run:
                print(config_to_json(project_config))
                raise typer.Exit(0)

            # Generate project
            generator = ProjectGenerator(project_config)
            project_path = generator.generate(output_dir, non_interactive=True)

            # Show next steps
            generator.print_next_steps(project_path)

        else:
            # Interactive mode: ask questions
            config_result = ask_project_questions()

            # Generate project
            generator = ProjectGenerator(config_result)
            project_path = generator.generate(output_dir)

            # Show next steps
            generator.print_next_steps(project_path)

    except KeyboardInterrupt:
        console.print("\n[yellow]Project creation cancelled.[/yellow]")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except FileExistsError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Error creating project: {e}[/red]")
        raise typer.Exit(1)
