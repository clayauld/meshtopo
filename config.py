"""
Configuration management for the Meshtopo gateway service.
"""

import yaml
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class MqttConfig:
    """MQTT broker configuration."""
    broker: str
    port: int
    username: str
    password: str
    topic: str


@dataclass
class CalTopoConfig:
    """CalTopo API configuration."""
    group: str


@dataclass
class NodeMapping:
    """Node mapping configuration."""
    device_id: str


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class Config:
    """Main configuration class."""
    mqtt: MqttConfig
    caltopo: CalTopoConfig
    nodes: Dict[str, NodeMapping]
    logging: LoggingConfig

    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
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
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML configuration: {e}")
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Config':
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
        required_sections = ['mqtt', 'caltopo', 'nodes']
        for section in required_sections:
            if section not in data:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate MQTT configuration
        mqtt_data = data['mqtt']
        required_mqtt_keys = ['broker', 'port', 'username', 'password', 'topic']
        for key in required_mqtt_keys:
            if key not in mqtt_data:
                raise ValueError(f"Missing required MQTT configuration: {key}")
        
        mqtt_config = MqttConfig(
            broker=mqtt_data['broker'],
            port=int(mqtt_data['port']),
            username=mqtt_data['username'],
            password=mqtt_data['password'],
            topic=mqtt_data['topic']
        )
        
        # Validate CalTopo configuration
        caltopo_data = data['caltopo']
        if 'group' not in caltopo_data:
            raise ValueError("Missing required CalTopo configuration: group")
        
        caltopo_config = CalTopoConfig(
            group=caltopo_data['group']
        )
        
        # Validate and process node mappings
        nodes_data = data['nodes']
        if not isinstance(nodes_data, dict):
            raise ValueError("Nodes configuration must be a dictionary")
        
        nodes = {}
        for node_id, node_config in nodes_data.items():
            if not isinstance(node_config, dict) or 'device_id' not in node_config:
                raise ValueError(f"Invalid node configuration for {node_id}: missing device_id")
            
            nodes[node_id] = NodeMapping(
                device_id=node_config['device_id']
            )
        
        # Process logging configuration (optional)
        logging_data = data.get('logging', {})
        logging_config = LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        return cls(
            mqtt=mqtt_config,
            caltopo=caltopo_config,
            nodes=nodes,
            logging=logging_config
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
            level=log_level,
            format=self.logging.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set specific loggers to appropriate levels
        logging.getLogger('paho.mqtt').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
