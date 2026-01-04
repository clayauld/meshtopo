# Module `gateway`

Meshtopo Gateway Service Entry Point

This module serves as the command-line entry point for the Meshtopo gateway.
It is responsible for:

1. Parsing command-line arguments (configuration file path).
2. Validating the security of the provided configuration path (traversal prevention).
3. Instantiating and running the `GatewayApp`.
4. Handling top-level exceptions and safe shutdown.

## Security Mechanisms

* **Path Validation:** To prevent directory traversal attacks (where a user might
    trick the application into reading sensitive files outside the application
    directory), this module enforces that the configuration file must reside within
    the application's working directory tree. It uses `os.path.commonpath` to
    verify this containment.

## Usage

    python gateway.py [config_file]

    Arguments:
        config_file    Path to configuration file (default: config/config.yaml)

## Functions

## `def main() -> None`

Main entry point for the gateway service.

Orchestrates the startup sequence:

1. Determines config path from args or default.
2. Validates config path security.
3. Checks file existence.
4. Initializes `GatewayApp`.
5. Runs the asyncio event loop.
