# Module `gateway`

Meshtopo Gateway Service

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks
with CalTopo mapping platforms, enabling real-time position tracking of field
assets.

Usage:
    python gateway.py [config_file]

Arguments:
    config_file    Path to configuration file (default: config.yaml)

## Functions

## `def main() -> None`

Main entry point for the gateway service.
Parses command-line arguments, enforces security constraints, and
initializes the main asyncio event loop for the GatewayApp.
