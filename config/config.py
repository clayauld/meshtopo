"""
Configuration management for the Meshtopo gateway service.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class MqttConfig:
    """MQTT broker configuration."""

    broker: str
    port: int
    username: str
    password: str
    topic: str
    use_internal_broker: bool = False


@dataclass
class CalTopoTeamApiConfig:
    """CalTopo Team API configuration."""

    enabled: bool = False
    credential_id: str = ""
    secret_key: str = ""


@dataclass
class OAuthConfig:
    """OAuth configuration for web UI authentication."""

    provider: str = "google"
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""


@dataclass
class CalTopoConfig:
    """CalTopo API configuration."""

    group: str
    map_id: str = ""
    team_api: CalTopoTeamApiConfig = field(default_factory=CalTopoTeamApiConfig)
    oauth: OAuthConfig = field(default_factory=OAuthConfig)


@dataclass
class SslServiceConfig:
    """SSL configuration for individual services."""

    enabled: bool = False
    subdomain: str = ""
    port: int = 443


@dataclass
class SslConfig:
    """SSL/TLS configuration."""

    enabled: bool = False
    email: str = ""
    domain: str = ""
    acme_challenge: str = "http"
    services: Dict[str, SslServiceConfig] = field(default_factory=dict)


@dataclass
class SessionConfig:
    """Session configuration."""

    timeout: int = 3600
    secure: bool = True
    httponly: bool = True


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    enabled: bool = True
    requests_per_minute: int = 60


@dataclass
class WebUiConfig:
    """Web UI configuration."""

    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    secret_key: str = ""
    session: SessionConfig = field(default_factory=SessionConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)


@dataclass
class FileLoggingConfig:
    """File logging configuration."""

    enabled: bool = False
    path: str = "/app/logs/meshtopo.log"
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class WebUiLoggingConfig:
    """Web UI specific logging configuration."""

    level: str = "INFO"
    access_log: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: FileLoggingConfig = field(default_factory=FileLoggingConfig)
    web_ui: WebUiLoggingConfig = field(default_factory=WebUiLoggingConfig)


@dataclass
class NodeMapping:
    """Node mapping configuration."""

    device_id: str


@dataclass
class Config:
    """Main configuration class."""

    mqtt: MqttConfig
    caltopo: CalTopoConfig
    nodes: Dict[str, NodeMapping]
    logging: LoggingConfig
    ssl: SslConfig = field(default_factory=SslConfig)
    web_ui: WebUiConfig = field(default_factory=WebUiConfig)

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
            use_internal_broker=mqtt_data.get("use_internal_broker", False),
        )

        # Validate CalTopo configuration
        caltopo_data = data["caltopo"]
        if "group" not in caltopo_data:
            raise ValueError("Missing required CalTopo configuration: group")

        # Process Team API configuration
        team_api_data = caltopo_data.get("team_api", {})
        team_api_config = CalTopoTeamApiConfig(
            enabled=team_api_data.get("enabled", False),
            credential_id=team_api_data.get("credential_id", ""),
            secret_key=team_api_data.get("secret_key", ""),
        )

        # Process OAuth configuration
        oauth_data = caltopo_data.get("oauth", {})
        oauth_config = OAuthConfig(
            provider=oauth_data.get("provider", "google"),
            client_id=oauth_data.get("client_id", ""),
            client_secret=oauth_data.get("client_secret", ""),
            redirect_uri=oauth_data.get("redirect_uri", ""),
        )

        caltopo_config = CalTopoConfig(
            group=caltopo_data["group"],
            map_id=caltopo_data.get("map_id", ""),
            team_api=team_api_config,
            oauth=oauth_config,
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

            nodes[node_id] = NodeMapping(device_id=node_config["device_id"])

        # Process SSL configuration (optional)
        ssl_data = data.get("ssl", {})
        ssl_services = {}
        for service_name, service_data in ssl_data.get("services", {}).items():
            ssl_services[service_name] = SslServiceConfig(
                enabled=service_data.get("enabled", False),
                subdomain=service_data.get("subdomain", ""),
                port=service_data.get("port", 443),
            )

        ssl_config = SslConfig(
            enabled=ssl_data.get("enabled", False),
            email=ssl_data.get("email", ""),
            domain=ssl_data.get("domain", ""),
            acme_challenge=ssl_data.get("acme_challenge", "http"),
            services=ssl_services,
        )

        # Process Web UI configuration (optional)
        web_ui_data = data.get("web_ui", {})
        session_data = web_ui_data.get("session", {})
        session_config = SessionConfig(
            timeout=session_data.get("timeout", 3600),
            secure=session_data.get("secure", True),
            httponly=session_data.get("httponly", True),
        )

        rate_limit_data = web_ui_data.get("rate_limit", {})
        rate_limit_config = RateLimitConfig(
            enabled=rate_limit_data.get("enabled", True),
            requests_per_minute=rate_limit_data.get("requests_per_minute", 60),
        )

        web_ui_config = WebUiConfig(
            enabled=web_ui_data.get("enabled", False),
            host=web_ui_data.get("host", "0.0.0.0"),
            port=web_ui_data.get("port", 8080),
            secret_key=web_ui_data.get("secret_key", ""),
            session=session_config,
            rate_limit=rate_limit_config,
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

        web_ui_logging_data = logging_data.get("web_ui", {})
        web_ui_logging_config = WebUiLoggingConfig(
            level=web_ui_logging_data.get("level", "INFO"),
            access_log=web_ui_logging_data.get("access_log", True),
        )

        logging_config = LoggingConfig(
            level=logging_data.get("level", "INFO"),
            format=logging_data.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            file=file_logging_config,
            web_ui=web_ui_logging_config,
        )

        return cls(
            mqtt=mqtt_config,
            caltopo=caltopo_config,
            nodes=nodes,
            logging=logging_config,
            ssl=ssl_config,
            web_ui=web_ui_config,
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
