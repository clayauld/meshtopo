"""
Configuration management for the Meshtopo gateway service using Pydantic.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

# Constants
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class MqttUser(BaseModel):
    """MQTT user configuration."""

    username: str
    password: SecretStr
    acl: str = "readwrite"


class MqttConfig(BaseModel):
    """MQTT broker configuration."""

    broker: str
    port: int = 1883
    username: str = ""
    password: SecretStr = SecretStr("")
    topic: str = "msh/US/2/json/+/+"
    keepalive: int = 60
    use_internal_broker: bool = False


class MqttBrokerConfig(BaseModel):
    """Internal MQTT broker configuration."""

    enabled: bool = False
    port: int = 1883
    websocket_port: int = 9001
    persistence: bool = True
    max_connections: int = 1000
    allow_anonymous: bool = False
    users: List[MqttUser] = Field(default_factory=list)
    acl_enabled: bool = False


class CalTopoConfig(BaseModel):
    """CalTopo API configuration."""

    connect_key: Optional[str] = None
    group: Optional[str] = None

    @property
    def has_connect_key(self) -> bool:
        """Check if connect_key is configured and valid."""
        return bool(self.connect_key and self.connect_key.strip())

    @property
    def has_group(self) -> bool:
        """Check if group is configured and valid."""
        return bool(self.group and self.group.strip())

    @model_validator(mode="after")  # type: ignore[misc]
    def check_at_least_one_mode(self) -> "CalTopoConfig":
        if not self.has_connect_key and not self.has_group:
            raise ValueError(
                "At least one of 'connect_key' or 'group' must be configured."
            )
        return self

    @field_validator("connect_key", "group", mode="before")  # type: ignore[misc]
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip() or None
        return v


class FileLoggingConfig(BaseModel):
    """File logging configuration."""

    enabled: bool = False
    path: str = "/app/logs/meshtopo.log"
    max_size: str = "10MB"
    backup_count: int = 5


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = _LOG_FORMAT
    file: FileLoggingConfig = Field(default_factory=FileLoggingConfig)


class NodeMapping(BaseModel):
    """Node mapping configuration."""

    device_id: str
    group: Optional[str] = None


class DeviceConfig(BaseModel):
    """Device management configuration."""

    allow_unknown_devices: bool = True


class StorageConfig(BaseModel):
    """Storage configuration."""

    db_path: str = "meshtopo_state.sqlite"


class Config(BaseModel):
    """Main configuration class."""

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
        Load configuration from a YAML file.
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data: Any = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML configuration: {e}")

        if isinstance(data, dict):
            return cls.model_validate(data)  # type: ignore[no-any-return]
        else:
            raise TypeError("Config file must be a dictionary")

    def get_node_device_id(self, node_id: str) -> Optional[str]:
        """
        Get the CalTopo device ID for a given Meshtastic node ID.
        """
        node_mapping = self.nodes.get(node_id)
        return node_mapping.device_id if node_mapping else None

    def get_node_group(self, node_id: str) -> Optional[str]:
        """
        Get the GROUP for a given Meshtastic node ID.
        """
        node_mapping = self.nodes.get(node_id)
        if node_mapping and node_mapping.group:
            return node_mapping.group
        return self.caltopo.group

    def setup_logging(self) -> None:
        """
        Configure logging based on the configuration.
        """
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)

        handlers: List[logging.Handler] = [logging.StreamHandler()]

        if self.logging.file.enabled:
            log_path = Path(self.logging.file.path)
            # Ensure log directory exists
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)

                # Parse max size (e.g. 10MB -> bytes)
                max_bytes = 10 * 1024 * 1024  # Default 10MB
                if self.logging.file.max_size:
                    # Simple parser for KB, MB
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
                # Fallback to stderr if file logging fails (e.g. permissions)
                print(f"Failed to setup file logging: {e}")

        logging.basicConfig(
            level=log_level,
            format=self.logging.format,
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=handlers,
            force=True,  # Ensure we override any existing config
        )

        logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
