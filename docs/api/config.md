# Module `config.config`

Configuration management for the Meshtopo gateway service using Pydantic.

## Classes

## `class CalTopoConfig`

CalTopo API integration configuration.

Requires either a personal connect key or a group ID (or both)
to authorize position updates.

### `def check_at_least_one_mode(self) -> 'CalTopoConfig'`

Validate that either a connect key or a group is configured.
One of these must be present to successfully send data to CalTopo.

## `class Config`

The root configuration object for the Meshtopo service.
Encapsulates all child configuration models.

### `def get_node_device_id(self, node_id: str) -> Optional[str]`

Resolve the CalTopo device ID for a Meshtastic node.

Args:
    node_id: The Meshtastic source node ID.

Returns:
    The mapped device ID string, or None if no specific mapping exists.

### `def get_node_group(self, node_id: str) -> Optional[str]`

Resolve the CalTopo group ID for a specific node.
Falls back to the global CalTopo group if no node-specific group is defined.

Args:
    node_id: The Meshtastic source node ID.

Returns:
    The group ID string to be used for this node.

### `def setup_logging(self) -> None`

Initialize the global logging system using settings from the current configuration.
Sets the log level, format, and configures rotating file handlers if enabled.

## `class DeviceConfig`

Settings for device discovery and management.

## `class FileLoggingConfig`

Settings for logging output to a rotating file.

Attributes:
    enabled: If True, writes logs to a file.
    path: Filesystem path for the log file.
    max_size: Maximum size of a single log file (e.g., '10MB', '500KB').
    backup_count: Number of rotated log files to retain.

## `class LoggingConfig`

General logging system configuration.

Attributes:
    level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR).
    format: Standard Python logging format string.
    file: Specific settings for file-based logging.

## `class MqttBrokerConfig`

Internal MQTT broker (Mosquitto) service configuration.

Attributes:
    enabled: Whether to start the internal broker service.
    port: Standard MQTT port (default: 1883).
    websocket_port: MQTT-over-WebSockets port (default: 9001).
    persistence: Enable/disable database persistence for messages.
    max_connections: Limit on concurrent broker connections.
    allow_anonymous: If True, allows connections without authentication.
    users: List of authorized MQTT users and their ACLs.
    acl_enabled: If True, enforces ACL rules for connected users.

## `class MqttConfig`

MQTT broker connection configuration.

Attributes:
    broker: Hostname or IP address of the MQTT broker.
    port: TCP port number for the MQTT broker (default: 1883).
    username: Optional username for broker authentication.
    password: Optional secret password for broker authentication.
    topic: MQTT topic filter to subscribe to (e.g., 'msh/US/2/json/+/+').
    keepalive: Keepalive interval in seconds (default: 60).
    use_internal_broker: If True, connects to the internal Mosquitto instance.

## `class MqttUser`

MQTT user configuration for the internal broker.

Attributes:
    username: The username for the MQTT user.
    password: The secret password for the MQTT user.
    acl: Access control level (e.g., 'readwrite', 'readonly'). Defaults to 'readwrite'.

## `class NodeMapping`

Configuration for mapping specific Meshtastic nodes to CalTopo markers.

Attributes:
    device_id: The custom ID to use in CalTopo for this node.
    group: Optional specific CalTopo group for this node's markers.

## `class StorageConfig`

Configuration for local state storage.
