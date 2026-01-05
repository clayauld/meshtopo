#!/usr/bin/env python3
"""
Meshtopo Gateway Service

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks
with CalTopo mapping platforms, enabling real-time position tracking of field
assets.


Usage:
    python gateway.py [config_file]

Arguments:
    config_file    Path to configuration file (default: config.yaml)
"""

import asyncio
import os
import sys
from pathlib import Path

from gateway_app import GatewayApp  # noqa: E402


def main() -> None:
    """
    Main entry point for the gateway service.
    Parses command-line arguments, enforces security constraints, and
    initializes the main asyncio event loop for the GatewayApp.
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

    # Security enforcement: Configuration files MUST be located within the
    # current working directory (project root) to prevent directory traversal
    # or execution with arbitrary system files.
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
