#!/usr/bin/env python3
"""
Meshtopo Gateway Service Entry Point

This module serves as the command-line entry point for the Meshtopo gateway.
It is responsible for:
1.  Parsing command-line arguments (configuration file path).
2.  Validating the security of the provided configuration path (traversal prevention).
3.  Instantiating and running the `GatewayApp`.
4.  Handling top-level exceptions and safe shutdown.

## Security Mechanisms
*   **Path Validation:** To prevent directory traversal attacks (where a user might
    trick the application into reading sensitive files outside the application
    directory), this module enforces that the configuration file must reside within
    the application's working directory tree. It uses `os.path.commonpath` to
    verify this containment.

## Usage
    python gateway.py [config_file]

    Arguments:
        config_file    Path to configuration file (default: config/config.yaml)
"""

import asyncio
import os
import sys
from pathlib import Path

from gateway_app import GatewayApp  # noqa: E402


def main() -> None:
    """
    Main entry point for the gateway service.

    Orchestrates the startup sequence:
    1.  Determines config path from args or default.
    2.  Validates config path security.
    3.  Checks file existence.
    4.  Initializes `GatewayApp`.
    5.  Runs the asyncio event loop.
    """
    # Get configuration file path from command line argument
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config/config.yaml"

    # Security check: Ensure config path is within application directory
    # resolving symlinks and absolute paths
    cwd = os.getcwd()
    abs_config_path = os.path.abspath(config_path)

    # Use os.path.commonpath to safely check directory containment
    # We put them in a list; commonpath returns the longest common sub-path.
    # If config is inside cwd, commonpath should be cwd.
    try:
        common_prefix = os.path.commonpath([cwd, abs_config_path])
    except ValueError:
        # Can happen on Windows if drives are different
        common_prefix = ""

    if common_prefix != cwd:
        print(
            f"Error: Configuration file must be within the application "
            f"directory ({cwd})"
        )
        print(f"Attempted path: {abs_config_path}")
        sys.exit(1)

    # Check if config file exists
    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("Please create a configuration file or specify a different path.")
        print("Example: python gateway.py config/config.yaml")
        sys.exit(1)

    # Create and start the gateway application
    app = GatewayApp(config_path)

    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
