"""
Configuration management for the Meshtopo gateway service using Pydantic.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

# Constants
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# Default log level if none specified
_DEFAULT_LOG_LEVEL = "INFO"


class MqttUser(BaseModel):
    """
    MQTT user configuration for the internal broker.

    Attributes:
        username: The username for the MQTT user.
        password: The secret password for the MQTT user.
        acl: Access control level (e.g., 'readwrite', 'readonly'). Defaults to 'readwrite'.
    """

    username: str
    password: SecretStr
    acl: str = "readwrite"


class MqttConfig(BaseModel):
    """
    MQTT broker connection configuration.

    Attributes:
        broker: Hostname or IP address of the MQTT broker.
        port: TCP port number for the MQTT broker (default: 1883).
        username: Optional username for broker authentication.
        password: Optional secret password for broker authentication.
        topic: MQTT topic filter to subscribe to (e.g., 'msh/US/2/json/+/+').
        keepalive: Keepalive interval in seconds (default: 60).
        use_internal_broker: If True, connects to the internal Mosquitto instance.
    """

    broker: str
    port: int = 1883
    username: str = ""
    password: SecretStr = SecretStr("")
    topic: str = "msh/US/2/json/+/+"
    keepalive: int = 60
    use_internal_broker: bool = False


class MqttBrokerConfig(BaseModel):
    """
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
    """

    enabled: bool = False
    port: int = 1883
    websocket_port: int = 9001
    persistence: bool = True
    max_connections: int = 1000
    allow_anonymous: bool = False
    users: List[MqttUser] = Field(default_factory=list)
    acl_enabled: bool = False


class CalTopoConfig(BaseModel):
    """
    CalTopo API integration configuration.

    Requires either a personal connect key or a group ID (or both)
    to authorize position updates.
    """

    connect_key: Optional[str] = None
    group: Optional[str] = None

    @property
    def has_connect_key(self) -> bool:
        """Check if a non-empty connect_key is configured."""
        return bool(self.connect_key and self.connect_key.strip())

    @property
    def has_group(self) -> bool:
        """Check if a non-empty group ID is configured."""
        return bool(self.group and self.group.strip())

    @model_validator(mode="after")
    def check_at_least_one_mode(self) -> "CalTopoConfig":
        """
        Validate that either a connect key or a group is configured.
        One of these must be present to successfully send data to CalTopo.
        """
        if not self.has_connect_key and not self.has_group:
            raise ValueError(
                "At least one of 'connect_key' or 'group' must be configured."
            )
        return self

    @field_validator("connect_key", "group", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Auto-strip whitespace from string inputs and convert empty strings to None."""
        if v is not None:
            return v.strip() or None
        return v


class FileLoggingConfig(BaseModel):
    """
    Settings for logging output to a rotating file.

    Attributes:
        enabled: If True, writes logs to a file.
        path: Filesystem path for the log file.
        max_size: Maximum size of a single log file (e.g., '10MB', '500KB').
        backup_count: Number of rotated log files to retain.
    """

    enabled: bool = False
    path: str = "/app/logs/meshtopo.log"
    max_size: str = "10MB"
    backup_count: int = 5


class LoggingConfig(BaseModel):
    """
    General logging system configuration.

    Attributes:
        level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR).
        format: Standard Python logging format string.
        file: Specific settings for file-based logging.
    """

    level: str = _DEFAULT_LOG_LEVEL
    format: str = _LOG_FORMAT
    file: FileLoggingConfig = Field(default_factory=FileLoggingConfig)


class NodeMapping(BaseModel):
    """
    Configuration for mapping specific Meshtastic nodes to CalTopo markers.

    Attributes:
        device_id: The custom ID to use in CalTopo for this node.
        group: Optional specific CalTopo group for this node's markers.
    """

    device_id: str
    group: Optional[str] = None


class DeviceConfig(BaseModel):
    """Settings for device discovery and management."""

    allow_unknown_devices: bool = True


class StorageConfig(BaseModel):
    """Configuration for local state storage."""

    db_path: str = "meshtopo_state.sqlite"


class Config(BaseModel):
    """
    The root configuration object for the Meshtopo service.
    Encapsulates all child configuration models.
    """

    mqtt: MqttConfig
    caltopo: CalTopoConfig
    nodes: Dict[str, NodeMapping] = Field(default_factory=dict)
    logging: LoggingConfig
    mqtt_broker: MqttBrokerConfig = Field(default_factory=MqttBrokerConfig)
    devices: DeviceConfig = Field(default_factory=DeviceConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from a YAML file and apply environment variable overrides.

        Args:
            config_path: Absolute or relative path to the config.yaml file.

        Returns:
            A populated and validated Config object.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the file contains invalid YAML.
            TypeError: If the YAML root is not a dictionary.
            pydantic.ValidationError: If the configuration fails validation.
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data: Any = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML configuration: {e}")

        if not isinstance(data, dict):
            raise TypeError("Config file must be a dictionary")

        # Initial validation from file data
        config = cls.model_validate(data)

        # Apply environment variable overrides (useful for Docker/CI)
        mqtt_host = os.getenv("MQTT_BROKER_HOST")
        if mqtt_host:
            config.mqtt.broker = mqtt_host

        mqtt_port = os.getenv("MQTT_BROKER_PORT")
        if mqtt_port:
            try:
                config.mqtt.port = int(mqtt_port)
            except ValueError:
                # Silently ignore invalid port environment variables
                pass

        # CalTopo specific overrides
        caltopo_key = os.getenv("CALTOPO_CONNECT_KEY")
        if caltopo_key:
            config.caltopo.connect_key = caltopo_key

        caltopo_group = os.getenv("CALTOPO_GROUP")
        if caltopo_group:
            config.caltopo.group = caltopo_group

        return config

    def _get_node_mapping(self, node_id: str) -> Optional[NodeMapping]:
        """
        Locate the mapping configuration for a given node ID,
        handling the optional '!' prefix used by Meshtastic.

        Args:
            node_id: The numeric or hex node ID (e.g., '!1234abcd' or '1234abcd').

        Returns:
            The NodeMapping object if found, otherwise None.
        """
        # Direct lookup (exact match)
        if node_id in self.nodes:
            return self.nodes[node_id]

        # Handle '!' prefix logic: users might configure with or without the '!'
        if node_id.startswith("!"):
            stripped_id = node_id[1:]
            if stripped_id in self.nodes:
                return self.nodes[stripped_id]
        else:
            prefixed_id = f"!{node_id}"
            if prefixed_id in self.nodes:
                return self.nodes[prefixed_id]

        return None

    def get_node_device_id(self, node_id: str) -> Optional[str]:
        """
        Resolve the CalTopo device ID for a Meshtastic node.

        Args:
            node_id: The Meshtastic source node ID.

        Returns:
            The mapped device ID string, or None if no specific mapping exists.
        """
        node_mapping = self._get_node_mapping(node_id)
        return node_mapping.device_id if node_mapping else None

    def get_node_group(self, node_id: str) -> Optional[str]:
        """
        Resolve the CalTopo group ID for a specific node.
        Falls back to the global CalTopo group if no node-specific group is defined.

        Args:
            node_id: The Meshtastic source node ID.

        Returns:
            The group ID string to be used for this node.
        """
        node_mapping = self._get_node_mapping(node_id)
        if node_mapping and node_mapping.group:
            return node_mapping.group
        return self.caltopo.group

    def setup_logging(self) -> None:
        """
        Initialize the global logging system using settings from the current configuration.
        Sets the log level, format, and configures rotating file handlers if enabled.
        """
        # Determine numeric log level from string (e.g., 'DEBUG')
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)

        # Standard console handler (stdout)
        handlers: List[logging.Handler] = [logging.StreamHandler()]

        # Optional rotating file logging
        if self.logging.file.enabled:
            log_path = Path(self.logging.file.path)
            try:
                # Ensure parent directories exist (e.g., /app/logs/)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                # Convert human-readable size string to bytes (default 10MB)
                max_bytes = 10 * 1024 * 1024
                if self.logging.file.max_size:
                    size_str = self.logging.file.max_size.upper()
                    if size_str.endswith("K") or size_str.endswith("KB"):
                        max_bytes = int(float(size_str.rstrip("KB")) * 1024)
                    elif size_str.endswith("M") or size_str.endswith("MB"):
                        max_bytes = int(float(size_str.rstrip("MB")) * 1024 * 1024)
                    else:
                        try:
                            max_bytes = int(size_str)
                        except ValueError:
                            pass

                from logging.handlers import RotatingFileHandler

                file_handler = RotatingFileHandler(
                    log_path,
                    maxBytes=max_bytes,
                    backupCount=self.logging.file.backup_count,
                )
                file_handler.setFormatter(logging.Formatter(self.logging.format))
                handlers.append(file_handler)
            except Exception as e:
                # Log error to stderr if file setup fails (crucial for container debugging)
                print(f"CRITICAL: Failed to setup file logging at {log_path}: {e}")

        # Apply basic configuration to the root logger
        logging.basicConfig(
            level=log_level,
            format=self.logging.format,
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=handlers,
            force=True,  # Mandatory to override existing configurations (e.g., from libraries)
        )

        # Suppress verbose loggers from dependencies to keep output clean
        logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
