#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Interactive prompts and question flow for project configuration."""

import sys
from dataclasses import dataclass, field
from typing import Optional

import questionary
from questionary import Choice, Style
from rich.console import Console

from pipecat_cli.registry import BotType, ServiceLoader, ServiceRegistry

console = Console()

# Custom style for cleaner, more minimal prompts (inspired by Vite)
custom_style = Style(
    [
        ("qmark", "fg:#00d7af bold"),  # Green question mark
        ("question", "bold"),  # Question text
        ("answer", "fg:#5fd7ff"),  # User's answer in cyan
        ("pointer", "fg:#00d7af bold"),  # Green pointer
        ("highlighted", "fg:#00d7af bold"),  # Selected item
        ("selected", "fg:#00d7af"),  # Selected in checkbox
        ("separator", "fg:#6c6c6c"),  # Dim separator
        ("instruction", "fg:#808080"),  # Instructions
        ("text", ""),  # Normal text
        ("disabled", "fg:#858585 italic"),  # Disabled choices
    ]
)


def replace_question_with_answer(question: str, answer: str | list[str]):
    """
    Replace the questionary output line with a checkmark version.
    Uses ANSI escape codes to move cursor up and overwrite the line.
    """
    if isinstance(answer, list):
        answer_str = ", ".join(answer)
    else:
        answer_str = str(answer)

    # ANSI escape codes:
    # \033[A = move cursor up one line
    # \033[2K = clear entire line
    # \r = carriage return to start of line
    sys.stdout.write("\033[A")  # Move up one line
    sys.stdout.write("\033[2K")  # Clear the line
    sys.stdout.write("\r")  # Go to start of line
    sys.stdout.flush()

    # Print the new line with checkmark
    console.print(f"[green]✔[/green] {question} [cyan]{answer_str}[/cyan]")


@dataclass
class ProjectConfig:
    """Configuration for a Pipecat project."""

    # Basic info
    project_name: str
    bot_type: BotType  # "web" or "telephony"

    # Transport
    transports: list[str] = field(default_factory=list)

    # Pipeline mode
    mode: str = "cascade"  # "cascade" or "realtime"

    # Services (for cascade mode)
    stt_service: Optional[str] = None
    llm_service: Optional[str] = None
    tts_service: Optional[str] = None

    # Realtime service
    realtime_service: Optional[str] = None

    # Client (for web/mobile bots)
    generate_client: bool = False
    client_framework: Optional[str] = None  # "react"
    client_server: Optional[str] = None  # "vite" or "nextjs"

    # Features
    video_input: bool = False
    video_output: bool = False
    recording: bool = False
    transcription: bool = False
    smart_turn: bool = False

    # Deployment
    deploy_to_cloud: bool = False
    enable_krisp: bool = False


def ask_project_questions() -> ProjectConfig:
    """
    Ask user for project configuration through interactive prompts.

    Returns:
        ProjectConfig with user's selections
    """
    console.print("[bold cyan]Let's create your Pipecat project![/bold cyan]\n")

    # Question 1: Project name
    project_name = questionary.text(
        "Project name:",
        style=custom_style,
        validate=lambda text: len(text) > 0 or "Project name cannot be empty",
    ).ask()

    if not project_name:
        raise KeyboardInterrupt("Project creation cancelled")

    replace_question_with_answer("Project name:", project_name)

    # Question 2: Bot type
    bot_type = questionary.select(
        "Bot type:",
        choices=[
            Choice(title="Web/Mobile", value="web"),
            Choice(title="Telephony", value="telephony"),
        ],
        style=custom_style,
    ).ask()

    if not bot_type:
        raise KeyboardInterrupt("Project creation cancelled")

    replace_question_with_answer("Bot type:", "Web/Mobile" if bot_type == "web" else "Telephony")

    # Question 2b: Client framework (only for web/mobile)
    generate_client = False
    client_framework = None
    client_server = None

    if bot_type == "web":
        client_framework = questionary.select(
            "Client framework:",
            choices=[
                Choice(title="React", value="react"),
                Choice(title="Vanilla JS", value="vanilla"),
                Choice(title="None (server only)", value="none"),
            ],
            style=custom_style,
        ).ask()

        if not client_framework:
            raise KeyboardInterrupt("Project creation cancelled")

        framework_display = {
            "react": "React",
            "vanilla": "Vanilla JS",
            "none": "None (server only)",
        }
        replace_question_with_answer(
            "Client framework:", framework_display.get(client_framework, client_framework)
        )

        if client_framework == "react":
            generate_client = True
            client_server = questionary.select(
                "React dev server:",
                choices=[
                    Choice(title="Vite", value="vite"),
                    Choice(title="Next.js", value="nextjs"),
                ],
                style=custom_style,
            ).ask()

            if not client_server:
                raise KeyboardInterrupt("Project creation cancelled")

            replace_question_with_answer(
                "React dev server:", "Vite" if client_server == "vite" else "Next.js"
            )
        elif client_framework == "vanilla":
            generate_client = True
            client_server = "vite"  # Vanilla JS always uses Vite
        else:
            client_framework = None  # Set to None if user chose "none"

    # Question 3: Primary transport selection
    transport_options = ServiceLoader.get_transport_options(bot_type)
    transport_choices = [
        Choice(
            title=svc.label,
            value=svc.value,
        )
        for svc in transport_options
    ]

    primary_transport = questionary.select(
        "Transport:",
        choices=transport_choices,
        style=custom_style,
    ).ask()

    if not primary_transport:
        raise KeyboardInterrupt("Project creation cancelled")

    transports = [primary_transport]

    # Get label for display
    primary_label = next(
        (svc.label for svc in transport_options if svc.value == primary_transport),
        primary_transport,
    )
    replace_question_with_answer("Transport:", primary_label)

    # Question 3b: Additional transport (different for web vs telephony)
    if bot_type == "web":
        # For web bots: offer to add another transport (commonly for local testing)
        add_backup = questionary.confirm(
            "Add another transport for local testing?",
            default=False,
            style=custom_style,
        ).ask()

        replace_question_with_answer(
            "Add another transport for local testing?", "Yes" if add_backup else "No"
        )

        if add_backup:
            # Filter out the already-selected primary transport
            backup_choices = [c for c in transport_choices if c.value != primary_transport]

            if backup_choices:
                backup_transport = questionary.select(
                    "Additional transport:",
                    choices=backup_choices,
                    style=custom_style,
                ).ask()

                if backup_transport:
                    transports.append(backup_transport)
                    backup_label = next(
                        (svc.label for svc in transport_options if svc.value == backup_transport),
                        backup_transport,
                    )
                    replace_question_with_answer("Additional transport:", backup_label)

    elif bot_type == "telephony":
        # For telephony bots: offer to add WebRTC for local testing
        add_webrtc = questionary.confirm(
            "Add a WebRTC transport for local testing?",
            default=False,
            style=custom_style,
        ).ask()

        replace_question_with_answer(
            "Add a WebRTC transport for local testing?", "Yes" if add_webrtc else "No"
        )

        if add_webrtc:
            webrtc_choices = [
                Choice(title="SmallWebRTC", value="smallwebrtc"),
                Choice(title="Daily", value="daily"),
            ]
            webrtc_transport = questionary.select(
                "WebRTC provider:",
                choices=webrtc_choices,
                style=custom_style,
            ).ask()

            if webrtc_transport:
                transports.append(webrtc_transport)
                replace_question_with_answer(
                    "WebRTC provider:",
                    "SmallWebRTC" if webrtc_transport == "smallwebrtc" else "Daily",
                )

    # Question 4: Pipeline mode
    mode = questionary.select(
        "Pipeline architecture:",
        choices=[
            Choice(title="Cascade (STT → LLM → TTS)", value="cascade"),
            Choice(title="Realtime (speech-to-speech)", value="realtime"),
        ],
        style=custom_style,
    ).ask()

    if not mode:
        raise KeyboardInterrupt("Project creation cancelled")

    replace_question_with_answer(
        "Pipeline architecture:",
        "Cascade (STT → LLM → TTS)" if mode == "cascade" else "Realtime (speech-to-speech)",
    )

    # Initialize config
    config = ProjectConfig(
        project_name=project_name,
        bot_type=bot_type,
        transports=transports,
        mode=mode,
        generate_client=generate_client,
        client_framework=client_framework,
        client_server=client_server,
    )

    # Conditional questions based on mode
    if mode == "cascade":
        # Question 5a: STT Service
        stt_choices = [
            Choice(
                title=svc.label,
                value=svc.value,
            )
            for svc in ServiceRegistry.STT_SERVICES
        ]
        config.stt_service = questionary.select(
            "Speech-to-Text:",
            choices=stt_choices,
            style=custom_style,
        ).ask()

        stt_label = next(
            (svc.label for svc in ServiceRegistry.STT_SERVICES if svc.value == config.stt_service),
            config.stt_service,
        )
        replace_question_with_answer("Speech-to-Text:", stt_label)

        # Question 5b: LLM Service
        llm_choices = [
            Choice(
                title=svc.label,
                value=svc.value,
            )
            for svc in ServiceRegistry.LLM_SERVICES
        ]
        config.llm_service = questionary.select(
            "Language model:",
            choices=llm_choices,
            style=custom_style,
        ).ask()

        llm_label = next(
            (svc.label for svc in ServiceRegistry.LLM_SERVICES if svc.value == config.llm_service),
            config.llm_service,
        )
        replace_question_with_answer("Language model:", llm_label)

        # Question 5c: TTS Service
        tts_choices = [
            Choice(
                title=svc.label,
                value=svc.value,
            )
            for svc in ServiceRegistry.TTS_SERVICES
        ]
        config.tts_service = questionary.select(
            "Text-to-Speech:",
            choices=tts_choices,
            style=custom_style,
        ).ask()

        tts_label = next(
            (svc.label for svc in ServiceRegistry.TTS_SERVICES if svc.value == config.tts_service),
            config.tts_service,
        )
        replace_question_with_answer("Text-to-Speech:", tts_label)

    else:  # realtime mode
        # Question 5d: Realtime Service
        realtime_choices = [
            Choice(
                title=svc.label,
                value=svc.value,
            )
            for svc in ServiceRegistry.REALTIME_SERVICES
        ]
        config.realtime_service = questionary.select(
            "Realtime service:",
            choices=realtime_choices,
            style=custom_style,
        ).ask()

        realtime_label = next(
            (
                svc.label
                for svc in ServiceRegistry.REALTIME_SERVICES
                if svc.value == config.realtime_service
            ),
            config.realtime_service,
        )
        replace_question_with_answer("Realtime service:", realtime_label)

    # Question 6: Video input (only for web/mobile bots)
    if config.bot_type == "web":
        config.video_input = questionary.confirm(
            "Video input?",
            default=False,
            style=custom_style,
        ).ask()
        replace_question_with_answer("Video input?", "Yes" if config.video_input else "No")
    else:
        # Telephony bots don't support video
        config.video_input = False

    # Question 7: Video output (only for web/mobile bots)
    if config.bot_type == "web":
        config.video_output = questionary.confirm(
            "Video output?",
            default=False,
            style=custom_style,
        ).ask()
        replace_question_with_answer("Video output?", "Yes" if config.video_output else "No")
    else:
        # Telephony bots don't support video
        config.video_output = False

    # Question 8: Recording
    config.recording = questionary.confirm(
        "Audio recording?",
        default=False,
        style=custom_style,
    ).ask()
    replace_question_with_answer("Audio recording?", "Yes" if config.recording else "No")

    # Question 9: Transcription
    config.transcription = questionary.confirm(
        "Transcription logging?",
        default=False,
        style=custom_style,
    ).ask()
    replace_question_with_answer("Transcription logging?", "Yes" if config.transcription else "No")

    # Question 10: Smart Turn V3 (only for cascade mode)
    if config.mode == "cascade":
        config.smart_turn = questionary.confirm(
            "Smart turn-taking? (recommended)",
            default=True,
            style=custom_style,
        ).ask()
        replace_question_with_answer("Smart turn-taking?", "Yes" if config.smart_turn else "No")
    else:
        # Realtime mode doesn't use smart turn
        config.smart_turn = False

    # Question 11: Pipecat Cloud deployment
    config.deploy_to_cloud = questionary.confirm(
        "Deploy to Pipecat Cloud?",
        default=True,
        style=custom_style,
    ).ask()
    replace_question_with_answer(
        "Deploy to Pipecat Cloud?", "Yes" if config.deploy_to_cloud else "No"
    )

    # Question 12: Krisp noise cancellation (only if deploying to cloud)
    if config.deploy_to_cloud:
        config.enable_krisp = questionary.confirm(
            "Enable Krisp noise cancellation?",
            default=False,
            style=custom_style,
        ).ask()
        replace_question_with_answer(
            "Enable Krisp noise cancellation?", "Yes" if config.enable_krisp else "No"
        )

    return config
