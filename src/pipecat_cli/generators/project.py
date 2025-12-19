#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Main project generator that orchestrates file creation."""

import shutil
import subprocess
from pathlib import Path

import questionary
from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

from pipecat_cli.prompts import ProjectConfig
from pipecat_cli.registry import ServiceLoader, ServiceRegistry

console = Console()


class ProjectGenerator:
    """Generates a complete Pipecat project from configuration."""

    def __init__(self, config: ProjectConfig):
        """
        Initialize the project generator.

        Args:
            config: Project configuration from user prompts
        """
        self.config = config
        self.env = Environment(
            loader=PackageLoader("pipecat_cli", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _prompt_for_new_name(self, output_dir: Path) -> str:
        """
        Prompt user for a new project name if the current one already exists.

        Args:
            output_dir: The output directory where projects are created

        Returns:
            A valid project name that doesn't conflict with existing directories
        """
        while True:
            console.print(
                f"\n[yellow]⚠️  Directory '{self.config.project_name}' already exists![/yellow]"
            )
            new_name = questionary.text(
                "Please enter a different project name:",
                default=f"{self.config.project_name}-new",
                validate=lambda text: len(text) > 0 or "Project name cannot be empty",
            ).ask()

            if not new_name:
                raise KeyboardInterrupt("Project creation cancelled")

            # Check if the new name is available
            new_path = output_dir / new_name
            if not new_path.exists():
                return new_name

            # If still exists, loop will continue and prompt again

    def generate(self, output_dir: Path | None = None) -> Path:
        """
        Generate the complete project structure.

        Args:
            output_dir: Optional directory to create project in (defaults to current dir)

        Returns:
            Path to the created project directory
        """
        # Determine output directory
        if output_dir is None:
            output_dir = Path.cwd()

        project_path = output_dir / self.config.project_name

        # Check if project already exists and prompt for new name if needed
        if project_path.exists():
            new_name = self._prompt_for_new_name(output_dir)
            self.config.project_name = new_name
            project_path = output_dir / new_name

        # Create project directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        server_path = project_path / "server"
        server_path.mkdir(exist_ok=True)

        # Create client directory if generating client
        if self.config.generate_client:
            client_path = project_path / "client"
            client_path.mkdir(exist_ok=True)

        # Generate all files silently (operations are fast)
        # 1. Generate bot.py (in server/)
        self._generate_bot_file(server_path)

        # 1b. Generate server.py and server_utils.py for Daily PSTN and Twilio + Daily SIP
        if (
            "daily_pstn_dialin" in self.config.transports
            or "daily_pstn_dialout" in self.config.transports
            or "twilio_daily_sip_dialin" in self.config.transports
            or "twilio_daily_sip_dialout" in self.config.transports
        ):
            self._generate_server_files(server_path)

        # 2. Generate pyproject.toml (in server/)
        self._generate_pyproject(server_path)

        # 3. Generate .env.example (in server/)
        self._generate_env_example(server_path)

        # 4. Generate .gitignore (at root)
        self._generate_gitignore(project_path)

        # 5. Generate README.md (at root)
        self._generate_readme(project_path)

        # 6. Generate Dockerfile (in server/ if deploying to cloud)
        if self.config.deploy_to_cloud:
            self._generate_dockerfile(server_path)

        # 7. Generate pcc-deploy.toml (in server/ if deploying to cloud)
        if self.config.deploy_to_cloud:
            self._generate_pcc_deploy(server_path)

        # 8. Generate client (if requested)
        if self.config.generate_client:
            self._generate_client(project_path / "client")

        # Format generated Python files with Ruff
        self._format_python_files(server_path)

        return project_path

    def _generate_server_files(self, project_path: Path) -> None:
        """Generate server.py and server_utils.py for Daily PSTN dial-out or Twilio + Daily SIP."""
        # Determine which templates to use based on transport type and mode
        if self.config.daily_pstn_mode:
            # Daily PSTN - only dial-out has server files (dial-in doesn't need them)
            if self.config.daily_pstn_mode == "dial-in":
                # Daily PSTN dial-in doesn't require server.py/server_utils.py
                return
            mode = self.config.daily_pstn_mode  # 'dial-out'
            server_template_name = f"server/server_pstn_{mode.replace('-', '')}.py.jinja2"
            utils_template_name = f"server/server_utils_pstn_{mode.replace('-', '')}.py.jinja2"
        elif self.config.twilio_daily_sip_mode:
            # Twilio + Daily SIP
            mode = self.config.twilio_daily_sip_mode  # 'dial-in' or 'dial-out'
            server_template_name = (
                f"server/server_twilio_daily_sip_{mode.replace('-', '')}.py.jinja2"
            )
            utils_template_name = (
                f"server/server_utils_twilio_daily_sip_{mode.replace('-', '')}.py.jinja2"
            )
        else:
            # Shouldn't happen, but provide a fallback
            return

        # Generate server.py
        server_template = self.env.get_template(server_template_name)
        server_content = server_template.render()
        (project_path / "server.py").write_text(server_content)

        # Generate server_utils.py
        utils_template = self.env.get_template(utils_template_name)
        utils_content = utils_template.render()
        (project_path / "server_utils.py").write_text(utils_content)

    def _needs_aiohttp_session(self) -> bool:
        """Check if any selected service requires an aiohttp session."""
        # Collect all selected services
        service_values = []

        if self.config.mode == "cascade":
            if self.config.stt_service:
                service_values.append(self.config.stt_service)
            if self.config.llm_service:
                service_values.append(self.config.llm_service)
            if self.config.tts_service:
                service_values.append(self.config.tts_service)
        else:
            if self.config.realtime_service:
                service_values.append(self.config.realtime_service)

        if self.config.video_service:
            service_values.append(self.config.video_service)

        # Check if any service config contains "session=" parameter
        for service_value in service_values:
            if service_value in ServiceRegistry.SERVICE_CONFIGS:
                config_str = ServiceRegistry.SERVICE_CONFIGS[service_value]
                # Check if the config contains session= or aiohttp_session=
                if "session=" in config_str or "aiohttp_session=" in config_str:
                    return True

        return False

    def _generate_bot_file(self, project_path: Path) -> None:
        """Generate the main bot.py file."""
        # Select template based on mode
        if self.config.mode == "cascade":
            template = self.env.get_template("server/bot_cascade.py.jinja2")
        else:
            template = self.env.get_template("server/bot_realtime.py.jinja2")

        # Prepare context for template
        services = {
            "transports": self.config.transports,
        }

        if self.config.mode == "cascade":
            services.update(
                {
                    "stt": self.config.stt_service,
                    "llm": self.config.llm_service,
                    "tts": self.config.tts_service,
                }
            )
        else:
            services["realtime"] = self.config.realtime_service

        # Add video service if present
        if self.config.video_service:
            services["video"] = self.config.video_service

        features = {
            "recording": self.config.recording,
            "transcription": self.config.transcription,
            "smart_turn": self.config.smart_turn,
            "observability": self.config.enable_observability,
        }

        # Get imports
        imports = ServiceLoader.get_imports_for_services(services, features, self.config.bot_type)

        # Check if we need aiohttp session and add import if needed
        needs_session = self._needs_aiohttp_session()
        if needs_session and "import aiohttp" not in imports:
            imports.insert(0, "import aiohttp")

        context = {
            "project_name": self.config.project_name,
            "imports": imports,
            "bot_type": self.config.bot_type,
            "transports": self.config.transports,
            "mode": self.config.mode,
            "stt_service": self.config.stt_service,
            "llm_service": self.config.llm_service,
            "tts_service": self.config.tts_service,
            "realtime_service": self.config.realtime_service,
            "video_service": self.config.video_service,
            "video_input": self.config.video_input,
            "video_output": self.config.video_output,
            "recording": self.config.recording,
            "transcription": self.config.transcription,
            "smart_turn": self.config.smart_turn,
            "enable_krisp": self.config.enable_krisp,
            "enable_observability": self.config.enable_observability,
            "service_configs": ServiceRegistry.SERVICE_CONFIGS,
            "daily_pstn_mode": self.config.daily_pstn_mode,
            "twilio_daily_sip_mode": self.config.twilio_daily_sip_mode,
            "needs_session": needs_session,
        }

        # Render and write
        content = template.render(**context)
        bot_file = project_path / "bot.py"
        bot_file.write_text(content)

    def _generate_pyproject(self, project_path: Path) -> None:
        """Generate pyproject.toml with dependencies."""
        template = self.env.get_template("server/pyproject.toml.jinja2")

        # Build pipecat-ai extras list using ServiceLoader
        services = {"transports": self.config.transports}

        if self.config.mode == "cascade":
            services.update(
                {
                    "stt": self.config.stt_service,
                    "llm": self.config.llm_service,
                    "tts": self.config.tts_service,
                }
            )
        else:
            services["realtime"] = self.config.realtime_service

        # Extract all required extras
        extras = ServiceLoader.extract_extras_for_services(services)

        # Add smart turn if enabled
        if self.config.smart_turn:
            extras.add("local-smart-turn-v3")

        # Build the pipecat-ai dependency string
        # No version constraint - will use latest from PyPI
        pipecat_extras = ",".join(sorted(extras))
        pipecat_dependency = f"pipecat-ai[{pipecat_extras}]"

        context = {
            "project_name": self.config.project_name,
            "pipecat_dependency": pipecat_dependency,
            "deploy_to_cloud": self.config.deploy_to_cloud,
            "enable_observability": self.config.enable_observability,
            "transports": self.config.transports,
        }

        content = template.render(**context)
        (project_path / "pyproject.toml").write_text(content)

    def _generate_env_example(self, project_path: Path) -> None:
        """Generate .env.example with required API keys."""
        template = self.env.get_template("server/env.example.jinja2")

        context = {
            "project_name": self.config.project_name,
            "transports": self.config.transports,
            "stt_service": self.config.stt_service,
            "llm_service": self.config.llm_service,
            "tts_service": self.config.tts_service,
            "realtime_service": self.config.realtime_service,
            "video_service": self.config.video_service,
            "daily_pstn_mode": self.config.daily_pstn_mode,
            "twilio_daily_sip_mode": self.config.twilio_daily_sip_mode,
        }

        content = template.render(**context)
        (project_path / ".env.example").write_text(content)

    def _generate_gitignore(self, project_path: Path) -> None:
        """Generate .gitignore file."""
        template = self.env.get_template("gitignore.jinja2")
        context = {
            "generate_client": self.config.generate_client,
        }
        content = template.render(**context)
        (project_path / ".gitignore").write_text(content)

    def _get_service_label(self, service_value: str | None, service_list: list) -> str | None:
        """Get human-readable label for a service value."""
        if not service_value:
            return None
        return next(
            (svc.label for svc in service_list if svc.value == service_value), service_value
        )

    def _generate_readme(self, project_path: Path) -> None:
        """Generate README.md with project-specific instructions."""
        template = self.env.get_template("README.md.jinja2")

        # Get human-readable labels for all services
        all_transports = ServiceRegistry.WEBRTC_TRANSPORTS + ServiceRegistry.TELEPHONY_TRANSPORTS

        # Get run commands and categorize transports
        run_commands = self._get_run_commands()
        telephony_transports = {"twilio", "telnyx", "plivo", "exotel"}
        webrtc_transports = {"smallwebrtc", "daily"}
        has_telephony = any(t in telephony_transports for t in self.config.transports)
        has_webrtc = any(t in webrtc_transports for t in self.config.transports)

        context = {
            "project_name": self.config.project_name,
            "bot_type": self.config.bot_type,
            "transports": self.config.transports,
            "transport_labels": [
                self._get_service_label(t, all_transports) for t in self.config.transports
            ],
            "mode": self.config.mode,
            "stt_service": self.config.stt_service,
            "stt_label": self._get_service_label(
                self.config.stt_service, ServiceRegistry.STT_SERVICES
            ),
            "llm_service": self.config.llm_service,
            "llm_label": self._get_service_label(
                self.config.llm_service, ServiceRegistry.LLM_SERVICES
            ),
            "tts_service": self.config.tts_service,
            "tts_label": self._get_service_label(
                self.config.tts_service, ServiceRegistry.TTS_SERVICES
            ),
            "realtime_service": self.config.realtime_service,
            "realtime_label": self._get_service_label(
                self.config.realtime_service, ServiceRegistry.REALTIME_SERVICES
            ),
            "video_input": self.config.video_input,
            "video_output": self.config.video_output,
            "recording": self.config.recording,
            "transcription": self.config.transcription,
            "smart_turn": self.config.smart_turn,
            "enable_krisp": self.config.enable_krisp,
            "enable_observability": self.config.enable_observability,
            "deploy_to_cloud": self.config.deploy_to_cloud,
            "generate_client": self.config.generate_client,
            "client_framework": self.config.client_framework,
            "client_server": self.config.client_server,
            "run_commands": run_commands,
            "has_telephony": has_telephony,
            "has_webrtc": has_webrtc,
            "daily_pstn_mode": self.config.daily_pstn_mode,
            "twilio_daily_sip_mode": self.config.twilio_daily_sip_mode,
        }

        content = template.render(**context)
        (project_path / "README.md").write_text(content)

    def _generate_dockerfile(self, project_path: Path) -> None:
        """Generate Dockerfile for Pipecat Cloud deployment."""
        template = self.env.get_template("server/Dockerfile.jinja2")

        context = {
            "transports": self.config.transports,
            "daily_pstn_mode": self.config.daily_pstn_mode,
            "twilio_daily_sip_mode": self.config.twilio_daily_sip_mode,
        }

        content = template.render(**context)
        (project_path / "Dockerfile").write_text(content)

    def _generate_pcc_deploy(self, project_path: Path) -> None:
        """Generate pcc-deploy.toml for Pipecat Cloud deployment."""
        template = self.env.get_template("server/pcc-deploy.toml.jinja2")

        context = {
            "project_name": self.config.project_name,
            "enable_krisp": self.config.enable_krisp,
        }

        content = template.render(**context)
        (project_path / "pcc-deploy.toml").write_text(content)

    def print_next_steps(self, project_path: Path) -> None:
        """Print next steps for the user."""
        console.print("\n[bold green]✨ Project created successfully![/bold green]")
        console.print(f"   [cyan]{project_path}[/cyan]\n")

        console.print("[bold]Next steps:[/bold]\n")
        console.print(
            f"  • Go to your project: [bold cyan]cd {self.config.project_name}[/bold cyan]"
        )

        # Check if this is Daily PSTN or Twilio + Daily SIP (special handling)
        is_daily_pstn = any(
            t in ["daily_pstn_dialin", "daily_pstn_dialout"] for t in self.config.transports
        )
        is_twilio_daily_sip = any(
            t in ["twilio_daily_sip_dialin", "twilio_daily_sip_dialout"]
            for t in self.config.transports
        )

        if is_daily_pstn or is_twilio_daily_sip:
            # Special instructions for Daily PSTN and Twilio + Daily SIP
            console.print("\n  [bold]Server setup:[/bold]")
            console.print("  • Go to server: [bold cyan]cd server[/bold cyan]")
            console.print("  • Install dependencies: [bold cyan]uv sync[/bold cyan]")
            console.print("  • Create .env file: [bold cyan]cp .env.example .env[/bold cyan]")
            console.print("  • [bold]Edit .env and add your API keys[/bold]")
            console.print("\n  [bold]See README.md for detailed setup instructions[/bold]")
            console.print("  • Configure webhooks/SIP domains as described in the README")
            console.print("  • Run the multi-terminal workflow (server.py + bot.py)")

            if self.config.deploy_to_cloud:
                console.print(
                    "\n[dim]See https://docs.pipecat.ai/deployment/pipecat-cloud for deployment info.[/dim]\n"
                )
            else:
                console.print(
                    "\n[dim]Check the README for local development and production deployment.[/dim]\n"
                )
            return

        # Determine run command based on transport
        run_commands = self._get_run_commands()

        # Client setup
        if self.config.generate_client:
            console.print("\n  [bold]Client setup:[/bold]")
            console.print(
                "  • Go to client: In a separate terminal window or tab [bold cyan]cd client[/bold cyan]"
            )
            console.print("  • Install dependencies: [bold cyan]npm install[/bold cyan]")
            console.print("  • Run dev server: [bold cyan]npm run dev[/bold cyan]")

        # Server setup
        console.print("\n  [bold]Server setup:[/bold]")
        console.print("  • Go to server: [bold cyan]cd server[/bold cyan]")
        console.print("  • Install dependencies: [bold cyan]uv sync[/bold cyan]")
        console.print("  • Create .env file: [bold cyan]cp .env.example .env[/bold cyan]")
        console.print("  • [bold]Edit .env and add your API keys[/bold]")

        # Categorize transports
        telephony_transports = {"twilio", "telnyx", "plivo", "exotel"}
        webrtc_transports = {"smallwebrtc", "daily"}

        has_telephony = any(t in telephony_transports for t in self.config.transports)
        has_webrtc = any(t in webrtc_transports for t in self.config.transports)

        # Get categorized commands
        webrtc_cmds = [cmd for cmd in run_commands if cmd["label"] in ["SmallWebRTC", "Daily"]]
        telephony_cmds = [
            cmd for cmd in run_commands if cmd["label"] in ["Twilio", "Telnyx", "Plivo", "Exotel"]
        ]

        if has_telephony and has_webrtc:
            # Mixed: show both local and production workflows
            console.print("  • Run your bot:\n")
            console.print("     [bold]For local development:[/bold]")
            for cmd in webrtc_cmds:
                console.print(f"       • {cmd['label']}: [bold cyan]{cmd['command']}[/bold cyan]")
            console.print("\n     [bold]For telephony deployment:[/bold]")
            console.print("       • Run ngrok: [bold cyan]ngrok http 7860[/bold cyan]")
            console.print("       • Run bot:")
            for cmd in telephony_cmds:
                console.print(f"         • {cmd['label']}: [bold cyan]{cmd['command']}[/bold cyan]")
        elif has_telephony:
            # Telephony only
            console.print("  • Run ngrok tunnel: [bold cyan]ngrok http 7860[/bold cyan]")
            console.print("  • Run your bot:")
            for cmd in run_commands:
                if cmd["label"]:
                    console.print(f"     • {cmd['label']}: [bold cyan]{cmd['command']}[/bold cyan]")
                else:
                    console.print(f"     [bold cyan]{cmd['command']}[/bold cyan]")
        else:
            # WebRTC only
            console.print("  • Run your bot:")
            for cmd in run_commands:
                if cmd["label"]:
                    console.print(f"     • {cmd['label']}: [bold cyan]{cmd['command']}[/bold cyan]")
                else:
                    console.print(f"     [bold cyan]{cmd['command']}[/bold cyan]")

        # Add cloud deployment info if applicable
        if self.config.deploy_to_cloud:
            console.print(
                "\n[dim]See https://docs.pipecat.ai/deployment/pipecat-cloud for deployment info.[/dim]\n"
            )
        else:
            console.print("\n[dim]See README.md for detailed setup instructions.[/dim]\n")

    def _get_run_commands(self) -> list[dict[str, str]]:
        """Get transport-specific run commands with labels."""
        commands = []

        for transport in self.config.transports:
            if transport == "smallwebrtc":
                commands.append({"label": "SmallWebRTC", "command": "uv run bot.py"})
            elif transport == "daily":
                commands.append({"label": "Daily", "command": "uv run bot.py --transport daily"})
            elif transport in {"twilio", "telnyx", "plivo", "exotel"}:
                commands.append(
                    {
                        "label": transport.title(),
                        "command": f"uv run bot.py --transport {transport} --proxy your_url.ngrok.io",
                    }
                )

        # If no specific commands, default to basic run
        if not commands:
            commands.append({"label": "", "command": "uv run bot.py"})

        return commands

    def _generate_client(self, client_path: Path) -> None:
        """Generate client application files."""
        # Determine which template to use
        # Determine template directory based on framework and server
        if self.config.client_framework == "react":
            if self.config.client_server == "vite":
                template_dir = "client/react-vite"
            elif self.config.client_server == "nextjs":
                template_dir = "client/react-nextjs"
            else:
                console.print(
                    f"[yellow]⚠️  Unknown client server: {self.config.client_server}[/yellow]"
                )
                return
        elif self.config.client_framework == "vanilla":
            # Vanilla JS always uses Vite
            template_dir = "client/vanilla-js-vite"
        else:
            console.print(
                f"[yellow]⚠️  Unknown client framework: {self.config.client_framework}[/yellow]"
            )
            return

        # Get the template directory path
        import pipecat_cli

        package_path = Path(pipecat_cli.__file__).parent
        source_template_dir = package_path / "templates" / template_dir

        if not source_template_dir.exists():
            console.print(f"[yellow]⚠️  Template not found: {source_template_dir}[/yellow]")
            return

        # Copy all files and render .jinja2 templates
        self._copy_and_render_directory(source_template_dir, client_path)

    def _copy_and_render_directory(self, source_dir: Path, dest_dir: Path) -> None:
        """
        Recursively copy directory contents, rendering .jinja2 templates.

        Args:
            source_dir: Source template directory
            dest_dir: Destination directory
        """
        for item in source_dir.rglob("*"):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(source_dir)

                # Skip SmallWebRTC-specific files if SmallWebRTC is not in transports
                if "smallwebrtc" not in self.config.transports:
                    # Skip the sessions API route for Next.js
                    if "api/sessions" in str(rel_path):
                        continue

                # Determine destination path
                if item.suffix == ".jinja2":
                    # Remove .jinja2 extension for rendered files
                    dest_file = dest_dir / str(rel_path)[: -len(".jinja2")]
                else:
                    dest_file = dest_dir / rel_path

                # Create parent directories
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Render or copy
                if item.suffix == ".jinja2":
                    self._render_client_template(item, dest_file)
                else:
                    shutil.copy2(item, dest_file)

    def _render_client_template(self, template_file: Path, dest_file: Path) -> None:
        """
        Render a Jinja2 template file with client-specific context.

        Only used for config.ts and package.json templates.
        Most TypeScript files are static and copied directly.

        Args:
            template_file: Path to .jinja2 template
            dest_file: Destination file path (without .jinja2)
        """
        # Create Jinja2 environment for this specific file
        template_content = template_file.read_text()
        from jinja2 import Template

        try:
            template = Template(template_content)
        except Exception as e:
            console.print(f"[red]Error rendering template {template_file.name}:[/red]")
            console.print(f"[red]{e}[/red]")
            raise

        # Prepare context - only need transport values and project name
        # Transform transport strings to objects for template iteration
        transport_objects = [{"value": t} for t in self.config.transports]

        context = {
            "project_name": self.config.project_name,
            "transports": transport_objects,
        }

        # Render and write
        rendered = template.render(**context)
        dest_file.write_text(rendered)

    def _format_python_files(self, project_path: Path) -> None:
        """Format generated Python files with Ruff."""
        try:
            # Run ruff format on the project directory
            subprocess.run(
                ["ruff", "format", str(project_path)],
                capture_output=True,
                check=False,  # Don't raise if ruff isn't installed
            )

            # Run ruff check --fix to organize imports
            subprocess.run(
                ["ruff", "check", "--fix", "--select", "I", str(project_path)],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            # Ruff not installed, skip formatting
            pass
