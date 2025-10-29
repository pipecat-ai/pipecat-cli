#!/usr/bin/env python3
"""
Auto-generate service initialization configurations.

This script inspects Pipecat service classes and generates SERVICE_CONFIGS
by analyzing constructor signatures and mapping parameters to environment variables.

Usage:
    uv run scripts/imports/config_generator.py [--preview]

Options:
    --preview    Show generated configs without writing to file
"""

import inspect
import sys
from pathlib import Path

# Add src and imports directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts" / "imports"))

from import_generator import find_class_in_directory  # type: ignore

from pipecat_cli.registry import ServiceRegistry
from pipecat_cli.registry.service_metadata import MANUAL_SERVICE_CONFIGS

# Parameter name -> environment variable suffix mapping
# Handles special cases where parameter names don't match env var conventions
PARAM_TO_ENV_SUFFIX = {
    "api_key": "API_KEY",
    "credentials": "APPLICATION_CREDENTIALS",
    "credentials_path": "TEST_CREDENTIALS",
    "region": "REGION",
    "region_name": "REGION",
    "voice_id": "VOICE_ID",
    "voice": "VOICE_ID",
    "replica_id": "REPLICA_ID",
    "face_id": "FACE_ID",
    "model": "MODEL",
    "base_url": "BASE_URL",
    "endpoint": "ENDPOINT",
    "hf_token": "HF_TOKEN",
    "aws_access_key_id": "ACCESS_KEY_ID",
    "aws_secret_access_key": "SECRET_ACCESS_KEY",
    "access_key_id": "ACCESS_KEY_ID",
    "secret_access_key": "SECRET_ACCESS_KEY",
    "session_token": "SESSION_TOKEN",
    "project_id": "PROJECT_ID",
    "location": "LOCATION",
    "system_instruction": "SYSTEM_INSTRUCTION",
    "instructions": "INSTRUCTIONS",
    "group_id": "GROUP_ID",
    "model_name": "MODEL_NAME",
}

# Parameters that should be hardcoded to specific values (not env vars)
HARDCODED_PARAMS = {
    "aiohttp_session": "session",
    "session": "session",
}


def get_service_class(service_value: str):
    """Import and return the service class for inspection."""
    try:
        # Find the service definition
        all_services = (
            ServiceRegistry.STT_SERVICES
            + ServiceRegistry.LLM_SERVICES
            + ServiceRegistry.TTS_SERVICES
            + ServiceRegistry.REALTIME_SERVICES
            + ServiceRegistry.VIDEO_SERVICES
        )

        service_def = next((s for s in all_services if s.value == service_value), None)
        if not service_def:
            return None

        class_names = service_def.class_name
        if not class_names:
            return None

        # Get the first class name (primary service class)
        class_name = class_names[0] if isinstance(class_names, list) else class_names

        # Import pipecat and find the class
        import pipecat

        pipecat_path = Path(pipecat.__file__).parent
        result = find_class_in_directory(pipecat_path / "services", class_name)

        if not result:
            return None

        file_path, module_path = result

        # Dynamically import the module and get the class
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    except Exception as e:
        print(f"  # Warning: Could not import {service_value}: {e}", file=sys.stderr)
        return None


def get_service_metadata(service_value: str) -> dict | None:
    """Get metadata for a service from the registry."""
    all_services = (
        ServiceRegistry.STT_SERVICES
        + ServiceRegistry.LLM_SERVICES
        + ServiceRegistry.TTS_SERVICES
        + ServiceRegistry.REALTIME_SERVICES
        + ServiceRegistry.VIDEO_SERVICES
    )

    service_def = next((s for s in all_services if s.value == service_value), None)
    return service_def


def get_env_var_name(service_value: str, param_name: str) -> str:
    """Generate environment variable name for a service parameter."""
    # Get prefix from service metadata
    service_meta = get_service_metadata(service_value)
    if service_meta and service_meta.env_prefix:
        prefix = service_meta.env_prefix
    else:
        # Fallback if metadata is missing
        prefix = service_value.upper()

    # Use mapped suffix if available, otherwise convert param name
    suffix = PARAM_TO_ENV_SUFFIX.get(param_name, param_name.upper())

    return f"{prefix}_{suffix}"


def should_skip_parameter(param_name: str, param: inspect.Parameter) -> bool:
    """Determine if a parameter should be skipped in generation."""
    # Skip self, *args, **kwargs
    if param_name in ("self", "args", "kwargs"):
        return True
    if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
        return True

    # Skip params that are hardcoded
    if param_name in HARDCODED_PARAMS:
        return False  # Don't skip, but will be handled specially

    return False


def generate_param_code(
    service_value: str, param_name: str, param: inspect.Parameter, is_multiline: bool = False
) -> str | None:
    """Generate the initialization code for a single parameter.

    Returns None if the parameter should be skipped.
    Includes:
    - Required parameters (no default)
    - Parameters listed in service metadata's include_params
    - Hardcoded parameters (like aiohttp_session)
    """
    # Handle hardcoded parameters (special cases like aiohttp_session)
    if param_name in HARDCODED_PARAMS:
        return f"{param_name}={HARDCODED_PARAMS[param_name]}"

    # Check if parameter has a default value
    has_default = param.default != inspect.Parameter.empty

    # Get the include list from service metadata
    service_meta = get_service_metadata(service_value)
    if service_meta and service_meta.include_params:
        include_list = service_meta.include_params
    else:
        # Fallback if metadata is missing
        include_list = []

    # Skip parameters with defaults UNLESS they're in this service's include list
    if has_default and param_name not in include_list:
        return None

    # Include this parameter - generate env var code
    env_var = get_env_var_name(service_value, param_name)

    # Special case: some services have empty string defaults that should be preserved
    # e.g., gladia_stt, asyncai_tts, inworld_tts, minimax_tts
    if has_default and param.default == "":
        return f'{param_name}=os.getenv("{env_var}", "")'

    return f'{param_name}=os.getenv("{env_var}")'


def get_all_init_parameters(service_class) -> dict[str, inspect.Parameter]:
    """Get all __init__ parameters including from parent classes.

    Walks up the inheritance chain to collect all parameters,
    with child class parameters overriding parent parameters.
    """
    all_params = {}

    # Walk the MRO (Method Resolution Order) in reverse to start with base classes
    for base_class in reversed(inspect.getmro(service_class)):
        # Skip object and other built-ins
        if base_class in (object, type):
            continue

        try:
            # Get the signature for this class's __init__
            sig = inspect.signature(base_class.__init__)
            # Update with this class's parameters (child overrides parent)
            all_params.update(sig.parameters)
        except (ValueError, TypeError):
            # Some classes might not have inspectable __init__
            continue

    return all_params


def generate_service_config(service_value: str) -> str | None:
    """Generate initialization code for a service by inspecting its class."""
    # Check if this service has manual_config flag in metadata
    service_meta = get_service_metadata(service_value)
    has_manual_flag = service_meta and getattr(service_meta, "manual_config", False)

    # Check if this is a special case that needs manual handling
    if has_manual_flag:
        print(
            f"  # Skipping {service_value} (special case - manual config required)", file=sys.stderr
        )
        return None

    service_class = get_service_class(service_value)
    if not service_class:
        print(f"  # Could not load class for {service_value}", file=sys.stderr)
        return None

    # Get class name
    class_name = service_class.__name__

    # Get all parameters including from parent classes
    try:
        all_params = get_all_init_parameters(service_class)
    except Exception as e:
        print(f"  # Could not inspect {class_name}: {e}", file=sys.stderr)
        return None

    # Generate parameter code
    param_codes = []
    for param_name, param in all_params.items():
        if should_skip_parameter(param_name, param):
            continue

        param_code = generate_param_code(service_value, param_name, param)
        if param_code:
            param_codes.append(param_code)

    # Format the initialization code
    if not param_codes:
        # No parameters (unlikely but handle it)
        return f"{class_name}()"
    elif len(param_codes) == 1:
        # Single parameter - keep on one line
        return f"{class_name}({param_codes[0]})"
    else:
        # Multiple parameters - format as multi-line
        lines = [f"{class_name}("]
        for i, code in enumerate(param_codes):
            comma = "," if i < len(param_codes) - 1 else ""
            lines.append(f"        {code}{comma}")
        lines.append("    )")
        return "\n".join(lines)


def generate_all_configs() -> dict[str, str]:
    """Generate configurations for all services."""
    configs = {}

    all_services = [
        ("STT", ServiceRegistry.STT_SERVICES),
        ("LLM", ServiceRegistry.LLM_SERVICES),
        ("TTS", ServiceRegistry.TTS_SERVICES),
        ("Realtime", ServiceRegistry.REALTIME_SERVICES),
        ("Video", ServiceRegistry.VIDEO_SERVICES),
    ]

    for service_type, services in all_services:
        print(f"\n# Generating {service_type} services...", file=sys.stderr)
        for service in services:
            service_value = service.value

            # Check if this service has a manual config
            if service_value in MANUAL_SERVICE_CONFIGS:
                configs[service_value] = MANUAL_SERVICE_CONFIGS[service_value]
                print(f"  ✓ {service_value} (manual config)", file=sys.stderr)
                continue

            # Otherwise, try to auto-generate
            config = generate_service_config(service_value)
            if config:
                configs[service_value] = config
                print(f"  ✓ {service_value}", file=sys.stderr)
            else:
                print(f"  ✗ {service_value} (skipped or failed)", file=sys.stderr)

    return configs


def format_config_dict(configs: dict[str, str]) -> str:
    """Format the configs dictionary as Python code."""
    lines = []
    lines.append("SERVICE_CONFIGS = {")

    # Group by service type
    categories = [
        ("# STT Services", ServiceRegistry.STT_SERVICES),
        ("# LLM Services", ServiceRegistry.LLM_SERVICES),
        ("# TTS Services", ServiceRegistry.TTS_SERVICES),
        ("# Realtime Services", ServiceRegistry.REALTIME_SERVICES),
        ("# Video Services", ServiceRegistry.VIDEO_SERVICES),
    ]

    for comment, services in categories:
        lines.append(f"    {comment}")
        for service in services:
            service_value = service.value
            if service_value in configs:
                config_code = configs[service_value]

                # Check if multi-line
                if "\n" in config_code:
                    # Multi-line config with implicit string concatenation
                    lines.append(f"    '{service_value}': (")
                    for line in config_code.split("\n"):
                        if line:
                            lines.append(f"        '{line}\\n'")
                    lines.append("    ),")
                else:
                    # Single-line config - use single quotes throughout
                    lines.append(f"    '{service_value}': '{config_code}',")

    lines.append("}")
    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate service configurations")
    parser.add_argument("--preview", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    print("=" * 80, file=sys.stderr)
    print("SERVICE CONFIG GENERATOR", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    # Generate configs
    configs = generate_all_configs()

    print(f"\n\n# Generated {len(configs)} service configurations", file=sys.stderr)

    # Format as Python code
    formatted = format_config_dict(configs)

    if args.preview:
        print("\n" + "=" * 80)
        print("PREVIEW OF GENERATED CONFIGS:")
        print("=" * 80)
        print(formatted)
    else:
        # Write to file
        output_file = project_root / "src" / "pipecat_cli" / "registry" / "_configs.py"

        header = '''"""
AUTO-GENERATED SERVICE CONFIGURATIONS

⚠️  DO NOT EDIT THIS FILE DIRECTLY ⚠️

This file is automatically generated from service_metadata.py.
To make changes, edit service_metadata.py and run:
  uv run scripts/configs/update_configs.py

Source: scripts/configs/config_generator.py
"""

'''

        output_file.write_text(header + formatted + "\n")
        print(f"\n✅ Wrote configurations to {output_file}", file=sys.stderr)

        # Format with ruff
        print("🔍 Formatting with ruff...", file=sys.stderr)
        import subprocess

        result = subprocess.run(
            ["ruff", "format", str(output_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ File formatted successfully", file=sys.stderr)
        else:
            print(f"⚠️  Formatting warning: {result.stderr}", file=sys.stderr)


if __name__ == "__main__":
    main()
