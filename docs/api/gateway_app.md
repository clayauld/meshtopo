# Module `gateway_app`

Main gateway application that orchestrates MQTT and CalTopo communication.

## Classes

## `class GatewayApp`

Main application class that orchestrates the gateway service.

### `def __init__(self, config_path: str = 'config/config.yaml')`

Initialize the gateway application.

Args:
    config_path: Path to the configuration file

### `def close(self) -> None`

Close all resources.

### `def initialize(self) -> bool`

Initialize the application components.

Returns:
    bool: True if initialization successful, False otherwise

### `def start(self) -> None`

Start the gateway service.

### `def stop(self) -> None`

Stop the gateway service gracefully.
