#!/usr/bin/env python3
"""
Automated Documentation Generator

This script parses the source code in `src/` and generates developer-focused
Markdown documentation in `docs/api/`. It uses introspection to ensure
the documentation is always in sync with the code.
"""

import importlib
import inspect
import os
import pkgutil
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, List, Optional

# Add src and root to path so we can import modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

OUTPUT_DIR = Path("docs/api")


def ensure_output_dir() -> None:
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_docstring(doc: Optional[str], indent: int = 0) -> str:
    """Format a docstring for Markdown, removing common indentation."""
    if not doc:
        return ""

    lines = doc.split("\n")
    # Remove empty leading/trailing lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    # Determine indentation of second line (first line usually has no indent)
    min_indent = 1000
    for line in lines[1:]:
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            if current_indent < min_indent:
                min_indent = current_indent

    if min_indent == 1000:
        min_indent = 0

    formatted_lines = [lines[0].strip()]
    for line in lines[1:]:
        formatted_lines.append(line[min_indent:].rstrip())

    return "\n".join(formatted_lines)


def get_signature(obj: Any) -> str:
    """Get the signature of a function or method."""
    try:
        sig = inspect.signature(obj)
        sig_str = str(sig)
        # Normalize memory addresses (e.g., 0x7f8b1c...) to 0x...
        sig_str = re.sub(r"0x[0-9a-fA-F]+", "0x...", sig_str)
        return sig_str
    except (ValueError, TypeError):
        return "(...)"


def document_function(func: Any, name: str, level: int = 2) -> str:
    """Generate Markdown for a function."""
    md = []
    sig = get_signature(func)
    md.append(f"{'#' * level} `def {name}{sig}`")
    md.append("")
    md.append(format_docstring(func.__doc__))
    md.append("")
    return "\n".join(md)


def document_class(cls: Any, name: str) -> str:
    """Generate Markdown for a class."""
    md = []
    # Skip private classes unless requested (but we want internal details so maybe keep them?)
    # For now, skip if starts with _ but not __init__

    md.append(f"## `class {name}`")
    md.append("")
    md.append(format_docstring(cls.__doc__))
    md.append("")

    # Document methods
    for member_name, member in inspect.getmembers(cls):
        if member_name.startswith('__') and member_name.endswith('__') and member_name != "__init__":
            continue

        if inspect.isfunction(member):
            # Skip Pydantic/external methods unless they are defined in the module we are likely documenting
            # or overrides.
            # A simpler heuristic for now: check if the function's module is "pydantic.*"
            if member.__module__ and (
                member.__module__.startswith("pydantic")
                or member.__module__.startswith("typing")
            ):
                continue

            md.append(document_function(member, member_name, level=3))

    return "\n".join(md)


def generate_module_doc(module_name: str) -> None:
    """Generate documentation for a single module."""
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        return

    md = []
    short_name = module_name.split(".")[-1]

    md.append(f"# Module `{module_name}`")

    doc = format_docstring(module.__doc__)
    if doc:
        md.append("")
        md.append(doc)

    # Classes
    classes = inspect.getmembers(module, inspect.isclass)
    # Filter classes defined in this module
    classes = [c for c in classes if c[1].__module__ == module_name]

    if classes:
        md.append("")
        md.append("## Classes")
        for name, cls in classes:
            md.append("")
            md.append(document_class(cls, name))

    # Functions
    functions = inspect.getmembers(module, inspect.isfunction)
    # Filter functions defined in this module
    functions = [f for f in functions if f[1].__module__ == module_name]

    if functions:
        md.append("")
        md.append("## Functions")
        for name, func in functions:
            md.append("")
            md.append(document_function(func, name))

    output_file = OUTPUT_DIR / f"{short_name}.md"

    # Clean up results: no triple blank lines, etc.
    content = "\n".join(md).strip() + "\n"
    # Replace 3+ newlines with 2
    content = re.sub(r"\n{3,}", "\n\n", content)
    new_content = content

    # Only write if content has changed to avoid triggering pre-commit "modified files"
    if output_file.exists():
        with open(output_file, "r") as f:
            if f.read() == new_content:
                return

    with open(output_file, "w") as f:
        f.write(new_content)

    print(f"Generated docs for {module_name} -> {output_file}")


def main() -> None:
    """Main entry point."""
    ensure_output_dir()

    # List of modules to document
    modules = [
        "gateway",
        "gateway_app",
        "caltopo_reporter",
        "mqtt_client",
        "persistent_dict",
        "utils",
        "config.config",
    ]

    for mod in modules:
        generate_module_doc(mod)


if __name__ == "__main__":
    main()
