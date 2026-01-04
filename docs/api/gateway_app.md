# Module `gateway_app`

Main gateway application that orchestrates MQTT and CalTopo communication.

## Classes

## `class GatewayApp`

Main application engine that orchestrates the Meshtastic-to-CalTopo gateway.

It manages the lifecycle of the MQTT client, handles state persistence for
node identification, and routes incoming position data to the CalTopo API.

### `def __init__(self, config_path: str = 'config/config.yaml')`

Initialize the gateway application instance.

Args:
    config_path: Filesystem path to the YAML configuration file.
                Defaults to 'config/config.yaml'.

### `def close(self) -> None`

Close all resources.

### `def initialize(self) -> bool`

Perform a comprehensive startup sequence for all application components.
This includes loading configuration, initializing the persistent database,
setting up HTTP clients, and preparing the MQTT subscriber.

Returns:
    bool: True if all components initialized successfully; False if a
          critical failure occurred.

### `def start(self) -> None`

Execute the primary application loop.
Initializes components and then enters a long-running state until
a stop signal or fatal error occurs.

### `def stop(self) -> None`

Stop the gateway service gracefully.
