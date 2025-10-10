#!/usr/bin/env python3
"""
Meshtopo Gateway Service

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks
with CalTopo mapping platforms, enabling real-time position tracking of field assets.

Usage:
    python gateway.py [config_file]

Arguments:
    config_file    Path to configuration file (default: config.yaml)
"""

import sys
from pathlib import Path

from gateway_app import GatewayApp


def main() -> None:
    """Main entry point for the gateway service."""
    # Get configuration file path from command line argument
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"

    # Check if config file exists
    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("Please create a configuration file or specify a different path.")
        print("Example: python gateway.py config.yaml")
        sys.exit(1)

    # Create and start the gateway application
    app = GatewayApp(config_path)

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
