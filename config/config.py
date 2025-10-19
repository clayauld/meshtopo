"""
Configuration management for the Meshtopo gateway service using Pydantic.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

# Constants
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class MqttUser(BaseModel):
    """MQTT user configuration."""

    username: str
    password: str
    acl: str = "readwrite"


class MqttConfig(BaseModel):
    """MQTT broker configuration."""

    broker: str
    port: int = 1883
    username: str = ""
    password: str = ""
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

    @model_validator(mode="after")  # type: ignore[misc]
    def check_at_least_one_mode(self) -> "CalTopoConfig":
        if not self.connect_key and not self.group:
            raise ValueError(
                "At least one of 'connect_key' or 'group' must be configured."
            )
        return self


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


class Config(BaseModel):
    """Main configuration class."""

    mqtt: MqttConfig
    caltopo: CalTopoConfig
    nodes: Dict[str, NodeMapping]
    logging: LoggingConfig
    mqtt_broker: MqttBrokerConfig = Field(default_factory=MqttBrokerConfig)
    devices: DeviceConfig = Field(default_factory=DeviceConfig)

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
            return cls.model_validate(data)  # type: ignore
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

        logging.basicConfig(
            level=log_level, format=self.logging.format, datefmt="%Y-%m-%d %H:%M:%S"
        )

        logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
