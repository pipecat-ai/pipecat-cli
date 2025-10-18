#!/usr/bin/env python3
"""
Core logic for generating import statements for Pipecat services.

This module contains shared functions used by both generate_imports.py
and update_imports.py to avoid duplication.
"""

import ast
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pipecat_cli.registry import ServiceRegistry


def find_service_class_in_file(file_path: Path, target_class_name: str | None = None) -> str | None:
    """
    Parse a Python file and find a class or function definition.

    Args:
        file_path: Path to Python file
        target_class_name: Specific class/function name to look for, or None to find any Service class

    Returns:
        Class/function name if found, None otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Look for class or function definitions (including async functions)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                # If we're looking for a specific name, match it exactly
                if target_class_name and node.name == target_class_name:
                    return node.name
                # Otherwise, find any class ending with "Service"
                elif (
                    not target_class_name
                    and isinstance(node, ast.ClassDef)
                    and node.name.endswith("Service")
                ):
                    return node.name

        return None
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
        print(f"  # Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return None


def find_class_in_directory(
    directory: Path, class_name: str, max_depth: int = 5
) -> tuple[Path, str] | None:
    """
    Recursively search for a class or function in a directory tree.

    Args:
        directory: Directory to search in
        class_name: Class or function name to find
        max_depth: Maximum recursion depth

    Returns:
        Tuple of (file_path, module_path) if found, None otherwise
    """
    if max_depth <= 0:
        return None

    try:
        for item in directory.iterdir():
            # Skip __pycache__ and hidden directories
            if item.name.startswith((".", "__pycache__")):
                continue

            if item.is_file() and item.suffix == ".py":
                # Check if this file contains the class
                found_class = find_service_class_in_file(item, class_name)
                if found_class:
                    # Build module path from file path
                    # We need to find where "pipecat" starts in the path
                    parts = item.parts
                    try:
                        pipecat_index = parts.index("pipecat")
                        # Build path from "pipecat" onwards, without .py extension
                        module_parts = parts[pipecat_index:]
                        module_path = ".".join(module_parts).replace(".py", "")
                        return (item, module_path)
                    except ValueError:
                        print(
                            f"  # Warning: Could not find 'pipecat' in path {item}", file=sys.stderr
                        )
                        return None

            elif item.is_dir():
                # Recursively search subdirectories
                result = find_class_in_directory(item, class_name, max_depth - 1)
                if result:
                    return result

    except (PermissionError, OSError) as e:
        print(f"  # Warning: Could not access {directory}: {e}", file=sys.stderr)

    return None


def find_pipecat_install_path() -> Path | None:
    """Find the installed pipecat package location."""
    try:
        import pipecat

        pipecat_path = Path(pipecat.__file__).parent
        print(f"# Found pipecat at: {pipecat_path}", file=sys.stderr)
        print(f"# Pipecat version: {pipecat.__version__}", file=sys.stderr)
        print(file=sys.stderr)
        return pipecat_path
    except ImportError:
        print("# ERROR: pipecat-ai not installed. Run: uv sync", file=sys.stderr)
        return None


def discover_import(
    identifier: str,
    pipecat_path: Path,
    class_names: list[str] | str | None = None,
    search_subdir: str | None = None,
) -> str | None:
    """
    Unified function to discover import statements for any pipecat component.

    Uses recursive directory search to find classes/functions anywhere in the codebase.

    Args:
        identifier: Component identifier (for error messages)
        pipecat_path: Path to pipecat installation
        class_names: Class/function name(s) to import (list or string)
        search_subdir: Optional subdirectory to search in (e.g., "services", "transports")

    Returns:
        Full import statement or None if not found
    """
    if not class_names:
        print(f"  # Warning: No class_name provided for {identifier}, skipping", file=sys.stderr)
        return None

    # Normalize to list
    classes = class_names if isinstance(class_names, list) else [class_names]

    # Use the first class name to find the file
    primary_class = classes[0]

    # Determine search directory
    search_dir = pipecat_path / search_subdir if search_subdir else pipecat_path

    # Search recursively for the class
    if search_dir.exists():
        result = find_class_in_directory(search_dir, primary_class)
        if result:
            _, module_path = result
            # Import all requested class names from the discovered module
            classes_str = ", ".join(classes)
            return f"from {module_path} import {classes_str}"

    print(
        f"  # Warning: Could not find class {primary_class} for {identifier} in {search_dir}",
        file=sys.stderr,
    )
    return None


def extract_package_name(package_str: str) -> str:
    """Extract package name from package string like 'pipecat-ai[deepgram]'."""
    if "[" in package_str:
        return package_str.split("[")[1].split("]")[0]
    # Services without extras
    return ""


def generate_imports_dict() -> dict[str, list[str]]:
    """Generate the complete IMPORTS dictionary for all services and transports."""
    pipecat_path = find_pipecat_install_path()
    if not pipecat_path:
        sys.exit(1)

    imports_dict = {}

    # Generate transport imports
    for transport_list in [ServiceRegistry.WEBRTC_TRANSPORTS, ServiceRegistry.TELEPHONY_TRANSPORTS]:
        for transport in transport_list:
            value = transport.value
            class_names = transport.class_name
            import_stmt = discover_import(value, pipecat_path, class_names, "transports")
            if import_stmt:
                imports_dict[value] = [import_stmt]

    # Generate imports for all service types
    for service_list in [
        ServiceRegistry.STT_SERVICES,
        ServiceRegistry.LLM_SERVICES,
        ServiceRegistry.TTS_SERVICES,
        ServiceRegistry.REALTIME_SERVICES,
    ]:
        for service in service_list:
            value = service.value
            class_names = service.class_name
            import_stmt = discover_import(value, pipecat_path, class_names, "services")
            if import_stmt:
                imports_dict[value] = [import_stmt]

    return imports_dict


def format_feature_imports(pipecat_path: Path) -> list[str]:
    """
    Format feature imports as lines of Python code.

    Auto-discovers module paths for each class name in features using the unified discover_import function.

    Args:
        pipecat_path: Path to pipecat installation

    Returns:
        List of formatted import lines
    """
    lines = []
    for feature_name, class_names in ServiceRegistry.FEATURE_DEFINITIONS.items():
        # Group classes by their discovered module path
        module_to_classes: dict[str, list[str]] = {}

        for class_name in class_names:
            # Try to find the class in the pipecat codebase (search entire pipecat directory)
            result = find_class_in_directory(pipecat_path, class_name)
            if result:
                _, module_path = result
                if module_path not in module_to_classes:
                    module_to_classes[module_path] = []
                module_to_classes[module_path].append(class_name)
            else:
                # External imports (like dotenv) - use as-is
                if module_path := _get_external_module_path(class_name):
                    if module_path not in module_to_classes:
                        module_to_classes[module_path] = []
                    module_to_classes[module_path].append(class_name)
                else:
                    print(
                        f"  # Warning: Could not find module for feature class {class_name}",
                        file=sys.stderr,
                    )

        # Generate import statements
        import_statements = []
        for module_path, classes in sorted(module_to_classes.items()):
            classes_str = ", ".join(classes)
            import_statements.append(f"from {module_path} import {classes_str}")

        if len(import_statements) == 1:
            # Single import - keep on one line
            lines.append(f'        "{feature_name}": ["{import_statements[0]}"],')
        else:
            # Multiple imports - format as multi-line list
            lines.append(f'        "{feature_name}": [')
            for stmt in import_statements:
                lines.append(f'            "{stmt}",')
            lines.append("        ],")

    return lines


def _get_external_module_path(class_name: str) -> str | None:
    """Get module path for external (non-pipecat) imports."""
    external_mappings = {
        "load_dotenv": "dotenv",
    }
    return external_mappings.get(class_name)


def format_imports_dict(imports_dict: dict[str, list[str]], pipecat_path: Path) -> str:
    """Format the complete imports dictionary as Python code."""
    lines = []
    lines.append("    IMPORTS = {")

    # Define service categories to process
    categories = [
        ("# Transports - WebRTC", ServiceRegistry.WEBRTC_TRANSPORTS),
        ("# Transports - Telephony", ServiceRegistry.TELEPHONY_TRANSPORTS),
        ("# STT Services", ServiceRegistry.STT_SERVICES),
        ("# LLM Services", ServiceRegistry.LLM_SERVICES),
        ("# TTS Services", ServiceRegistry.TTS_SERVICES),
        ("# Realtime Services", ServiceRegistry.REALTIME_SERVICES),
    ]

    # Process each category
    for comment, services in categories:
        lines.append(f"        {comment}")
        for service in services:
            service_value = service.value
            if service_value in imports_dict:
                import_stmt = imports_dict[service_value][0]
                lines.append(f'        "{service_value}": ["{import_stmt}"],')

    lines.append("    }")
    lines.append("")
    lines.append("    # Additional imports for features (generated from FEATURE_DEFINITIONS)")
    lines.append("    FEATURE_IMPORTS = {")
    lines.extend(format_feature_imports(pipecat_path))
    lines.append("    }")

    return "\n".join(lines)
