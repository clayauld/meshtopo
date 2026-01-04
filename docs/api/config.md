# Module `config.config`

Configuration Management with Pydantic

This module defines the configuration schema for the Meshtopo gateway.
It uses `pydantic` for robust data validation, type coercion, and setting management.

## Features

* **Type Safety:** All configuration fields are strictly typed.
* **Secret Management:** Sensitive fields (passwords) use `SecretStr` to prevent
    accidental exposure in logs or `repr()`.
* **Environment Overrides:** Configuration values can be overridden by environment
    variables (e.g., `MQTT_BROKER_HOST`, `CALTOPO_CONNECT_KEY`) at runtime.
    This is essential for containerized deployments.
* **Validation:** Custom validators ensure data integrity (e.g., ensuring at least
    one CalTopo mode is enabled).

## Usage

    config = Config.from_file("config.yaml")
    print(config.mqtt.broker)

## Classes

## `class CalTopoConfig`

CalTopo API configuration.

### `def check_at_least_one_mode(self) -> 'CalTopoConfig'`

Validator: Ensure at least one reporting mode is active.

## `class Config`

Main configuration class.

### `def get_node_device_id(self, node_id: str) -> Optional[str]`

Get the CalTopo device ID for a given Meshtastic node ID.

### `def get_node_group(self, node_id: str) -> Optional[str]`

Get the GROUP for a given Meshtastic node ID.

### `def setup_logging(self) -> None`

Configure logging based on the configuration.
Sets up StreamHandler (console) and optional RotatingFileHandler.

## `class DeviceConfig`

Device management configuration.

## `class FileLoggingConfig`

File logging configuration.

## `class LoggingConfig`

Logging configuration.

## `class MqttBrokerConfig`

Internal MQTT broker configuration.

## `class MqttConfig`

MQTT broker configuration.

## `class MqttUser`

MQTT user configuration.

## `class NodeMapping`

Node mapping configuration.

## `class StorageConfig`

Storage configuration.
