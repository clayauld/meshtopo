"""
Configuration management for the Meshtopo gateway service.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class MqttUser:
    """MQTT user configuration."""

    username: str
    password: str
    acl: str = "readwrite"  # "read", "write", "readwrite"


@dataclass
class MqttConfig:
    """MQTT broker configuration."""

    broker: str
    port: int = 1883
    username: str = ""
    password: str = ""
    topic: str = "msh/US/2/json/+/+"
    keepalive: int = 60
    use_internal_broker: bool = False


@dataclass
class MqttBrokerConfig:
    """Internal MQTT broker configuration."""

    enabled: bool = False
    port: int = 1883
    websocket_port: int = 9001
    persistence: bool = True
    max_connections: int = 1000
    allow_anonymous: bool = False
    users: List[MqttUser] = field(default_factory=list)
    acl_enabled: bool = False


@dataclass
class CalTopoConfig:
    """CalTopo API configuration."""

    connect_key: str
    api_mode: str = "connect_key"  # "connect_key" or "group"
    group: Optional[str] = None


@dataclass
class FileLoggingConfig:
    """File logging configuration."""

    enabled: bool = False
    path: str = "/app/logs/meshtopo.log"
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: FileLoggingConfig = field(default_factory=FileLoggingConfig)


@dataclass
class NodeMapping:
    """Node mapping configuration."""

    device_id: str
    group: Optional[str] = None


@dataclass
class DeviceConfig:
    """Device management configuration."""

    allow_unknown_devices: bool = True


@dataclass
class Config:
    """Main configuration class."""

    mqtt: MqttConfig
    caltopo: CalTopoConfig
    nodes: Dict[str, NodeMapping]
    logging: LoggingConfig
    mqtt_broker: MqttBrokerConfig = field(default_factory=MqttBrokerConfig)
    devices: DeviceConfig = field(default_factory=DeviceConfig)

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Config: Loaded configuration object

        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
            ValueError: If required configuration is missing
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML configuration: {e}")

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create Config object from dictionary data.

        Args:
            data: Configuration data dictionary

        Returns:
            Config: Configuration object

        Raises:
            ValueError: If required configuration is missing
        """
        # Validate required sections
        required_sections = ["mqtt", "caltopo", "nodes"]
        for section in required_sections:
            if section not in data:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate MQTT configuration
        mqtt_data = data["mqtt"]
        required_mqtt_keys = ["broker", "port", "username", "password", "topic"]
        for key in required_mqtt_keys:
            if key not in mqtt_data:
                raise ValueError(f"Missing required MQTT configuration: {key}")

        mqtt_config = MqttConfig(
            broker=mqtt_data["broker"],
            port=int(mqtt_data["port"]),
            username=mqtt_data["username"],
            password=mqtt_data["password"],
            topic=mqtt_data["topic"],
            keepalive=int(mqtt_data.get("keepalive", 60)),
            use_internal_broker=mqtt_data.get("use_internal_broker", False),
        )

        # Validate CalTopo configuration
        caltopo_data = data["caltopo"]
        if "connect_key" not in caltopo_data:
            raise ValueError("Missing required CalTopo configuration: connect_key")

        api_mode = caltopo_data.get("api_mode", "connect_key")
        if api_mode not in ["connect_key", "group"]:
            raise ValueError("CalTopo api_mode must be 'connect_key' or 'group'")

        if api_mode == "connect_key":
            # connect_key mode - connect_key is required
            caltopo_config = CalTopoConfig(
                connect_key=caltopo_data["connect_key"],
                api_mode=api_mode,
                group=caltopo_data.get("group"),
            )
        else:
            # group mode - group is required
            if "group" not in caltopo_data:
                raise ValueError("CalTopo group is required when api_mode is 'group'")
            caltopo_config = CalTopoConfig(
                connect_key=caltopo_data["connect_key"],
                api_mode=api_mode,
                group=caltopo_data["group"],
            )

        # Validate and process node mappings
        nodes_data = data["nodes"]
        if not isinstance(nodes_data, dict):
            raise ValueError("Nodes configuration must be a dictionary")

        nodes = {}
        for node_id, node_config in nodes_data.items():
            if not isinstance(node_config, dict) or "device_id" not in node_config:
                raise ValueError(
                    f"Invalid node configuration for {node_id}: missing device_id"
                )

            nodes[node_id] = NodeMapping(
                device_id=node_config["device_id"],
                group=node_config.get("group"),
            )

        # Process logging configuration (optional)
        logging_data = data.get("logging", {})
        file_data = logging_data.get("file", {})
        file_logging_config = FileLoggingConfig(
            enabled=file_data.get("enabled", False),
            path=file_data.get("path", "/app/logs/meshtopo.log"),
            max_size=file_data.get("max_size", "10MB"),
            backup_count=file_data.get("backup_count", 5),
        )

        logging_config = LoggingConfig(
            level=logging_data.get("level", "INFO"),
            format=logging_data.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            file=file_logging_config,
        )

        # Process MQTT broker configuration (optional)
        mqtt_broker_data = data.get("mqtt_broker", {})
        mqtt_users = []
        for user_data in mqtt_broker_data.get("users", []):
            if isinstance(user_data, dict):
                mqtt_user = MqttUser(
                    username=user_data.get("username", ""),
                    password=user_data.get("password", ""),
                    acl=user_data.get("acl", "readwrite"),
                )
                mqtt_users.append(mqtt_user)

        mqtt_broker_config = MqttBrokerConfig(
            enabled=mqtt_broker_data.get("enabled", False),
            port=mqtt_broker_data.get("port", 1883),
            websocket_port=mqtt_broker_data.get("websocket_port", 9001),
            persistence=mqtt_broker_data.get("persistence", True),
            max_connections=mqtt_broker_data.get("max_connections", 1000),
            allow_anonymous=mqtt_broker_data.get("allow_anonymous", False),
            users=mqtt_users,
            acl_enabled=mqtt_broker_data.get("acl_enabled", False),
        )

        # Process device configuration (optional)
        devices_data = data.get("devices", {})
        device_config = DeviceConfig(
            allow_unknown_devices=devices_data.get("allow_unknown_devices", True),
        )

        return cls(
            mqtt=mqtt_config,
            caltopo=caltopo_config,
            nodes=nodes,
            logging=logging_config,
            mqtt_broker=mqtt_broker_config,
            devices=device_config,
        )

    def get_node_device_id(self, node_id: str) -> Optional[str]:
        """
        Get the CalTopo device ID for a given Meshtastic node ID.

        Args:
            node_id: Meshtastic hardware node ID

        Returns:
            str: CalTopo device ID if mapped, None otherwise
        """
        node_mapping = self.nodes.get(node_id)
        return node_mapping.device_id if node_mapping else None

    def get_node_group(self, node_id: str) -> Optional[str]:
        """
        Get the GROUP for a given Meshtastic node ID.

        Checks for per-device GROUP override first, then falls back to global GROUP.

        Args:
            node_id: Meshtastic hardware node ID

        Returns:
            str: GROUP if configured (per-device or global), None otherwise
        """
        # Check for per-device GROUP override
        node_mapping = self.nodes.get(node_id)
        if node_mapping and node_mapping.group:
            return node_mapping.group

        # Fall back to global GROUP
        return self.caltopo.group

    def setup_logging(self) -> None:
        """
        Configure logging based on the configuration.
        """
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level, format=self.logging.format, datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Set specific loggers to appropriate levels
        logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
