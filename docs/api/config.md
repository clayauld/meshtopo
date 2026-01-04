# Module `config.config`

Configuration management for the Meshtopo gateway service using Pydantic.

## Classes

## `class CalTopoConfig`

CalTopo API configuration.

### `def check_at_least_one_mode(self) -> 'CalTopoConfig'`

Validate that either a connect key or a group is configured.

## `class Config`

Main configuration class.

### `def get_node_device_id(self, node_id: str) -> Optional[str]`

Get the CalTopo device ID for a given Meshtastic node ID.

### `def get_node_group(self, node_id: str) -> Optional[str]`

Get the GROUP for a given Meshtastic node ID.

### `def setup_logging(self) -> None`

Configure logging based on the configuration.

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
