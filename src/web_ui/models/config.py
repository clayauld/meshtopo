"""
Configuration state management for web UI.
"""

import logging
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration state management."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config_cache = None

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            dict: Configuration data
        """
        try:
            if self._config_cache is None:
                self._load_config()

            return self._config_cache.copy()

        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return {}

    def _load_config(self):
        """Load configuration from file."""
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                self._config_cache = {}
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config_cache = yaml.safe_load(f)

            logger.debug("Configuration loaded from file")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config_cache = {}

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.

        Args:
            updates: Configuration updates

        Returns:
            bool: True if update successful
        """
        try:
            # Load current configuration
            current_config = self.get_config()

            # Apply updates
            self._deep_update(current_config, updates)

            # Save updated configuration
            self._save_config(current_config)

            # Update cache
            self._config_cache = current_config

            logger.info("Configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """
        Deep update dictionary with nested values.

        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _save_config(self, config: Dict[str, Any]):
        """
        Save configuration to file.

        Args:
            config: Configuration data to save
        """
        try:
            # Create backup of current config
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(".yaml.backup")
                self.config_path.rename(backup_path)

            # Write new configuration
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info("Configuration saved to file")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration.

        Returns:
            dict: Validation results
        """
        try:
            config = self.get_config()
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }

            # Validate required sections
            required_sections = ["mqtt", "caltopo", "nodes"]
            for section in required_sections:
                if section not in config:
                    validation_result["errors"].append(f"Missing required section: {section}")
                    validation_result["valid"] = False

            # Validate MQTT configuration
            if "mqtt" in config:
                mqtt_config = config["mqtt"]
                required_mqtt_keys = ["broker", "port", "username", "password", "topic"]
                for key in required_mqtt_keys:
                    if key not in mqtt_config:
                        validation_result["errors"].append(f"Missing required MQTT setting: {key}")
                        validation_result["valid"] = False

            # Validate CalTopo configuration
            if "caltopo" in config:
                caltopo_config = config["caltopo"]
                if "group" not in caltopo_config:
                    validation_result["errors"].append("Missing required CalTopo setting: group")
                    validation_result["valid"] = False

                # Check Team API configuration
                if caltopo_config.get("team_api", {}).get("enabled"):
                    team_api = caltopo_config["team_api"]
                    if not team_api.get("credential_id"):
                        validation_result["warnings"].append("CalTopo Team API enabled but credential_id not set")
                    if not team_api.get("secret_key"):
                        validation_result["warnings"].append("CalTopo Team API enabled but secret_key not set")

            # Validate Web UI configuration
            if config.get("web_ui", {}).get("enabled"):
                web_ui_config = config["web_ui"]
                if not web_ui_config.get("secret_key"):
                    validation_result["warnings"].append("Web UI enabled but secret_key not set")

            # Validate SSL configuration
            if config.get("ssl", {}).get("enabled"):
                ssl_config = config["ssl"]
                if not ssl_config.get("email"):
                    validation_result["warnings"].append("SSL enabled but email not set")
                if not ssl_config.get("domain"):
                    validation_result["warnings"].append("SSL enabled but domain not set")

            logger.info(f"Configuration validation completed: {validation_result['valid']}")
            return validation_result

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": []
            }

    def reset_config(self) -> bool:
        """
        Reset configuration to defaults.

        Returns:
            bool: True if reset successful
        """
        try:
            # Load default configuration from example file
            example_path = self.config_path.parent / "config.yaml.example"

            if not example_path.exists():
                logger.error("Example configuration file not found")
                return False

            with open(example_path, "r", encoding="utf-8") as f:
                default_config = yaml.safe_load(f)

            # Save as current configuration
            self._save_config(default_config)
            self._config_cache = default_config

            logger.info("Configuration reset to defaults")
            return True

        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False

    def backup_config(self) -> Dict[str, Any]:
        """
        Export configuration as backup.

        Returns:
            dict: Configuration backup data
        """
        try:
            config = self.get_config()

            backup_data = {
                "config": config,
                "timestamp": time.time(),
                "version": "1.0"
            }

            logger.info("Configuration backup created")
            return backup_data

        except Exception as e:
            logger.error(f"Failed to create configuration backup: {e}")
            return {}

    def restore_config(self, backup_data: Dict[str, Any]) -> bool:
        """
        Restore configuration from backup.

        Args:
            backup_data: Configuration backup data

        Returns:
            bool: True if restore successful
        """
        try:
            config = backup_data.get("config")

            if not config:
                logger.error("No configuration data in backup")
                return False

            # Save restored configuration
            self._save_config(config)
            self._config_cache = config

            logger.info("Configuration restored from backup")
            return True

        except Exception as e:
            logger.error(f"Failed to restore configuration: {e}")
            return False

    def get_current_map(self) -> Optional[Dict[str, Any]]:
        """
        Get currently selected map configuration.

        Returns:
            dict: Current map configuration or None
        """
        try:
            config = self.get_config()
            caltopo_config = config.get("caltopo", {})

            map_id = caltopo_config.get("map_id")
            if not map_id:
                return None

            return {
                "map_id": map_id,
                "group": caltopo_config.get("group"),
                "team_api_enabled": caltopo_config.get("team_api", {}).get("enabled", False)
            }

        except Exception as e:
            logger.error(f"Failed to get current map: {e}")
            return None

    def select_map(self, map_id: str) -> bool:
        """
        Select target map for position forwarding.

        Args:
            map_id: CalTopo map identifier

        Returns:
            bool: True if selection successful
        """
        try:
            updates = {
                "caltopo": {
                    "map_id": map_id
                }
            }

            return self.update_config(updates)

        except Exception as e:
            logger.error(f"Failed to select map {map_id}: {e}")
            return False

    def get_map_status(self, map_id: str) -> Dict[str, Any]:
        """
        Get real-time status of map integration.

        Args:
            map_id: CalTopo map identifier

        Returns:
            dict: Map status information
        """
        try:
            current_map = self.get_current_map()

            status = {
                "map_id": map_id,
                "selected": current_map and current_map.get("map_id") == map_id,
                "group": current_map.get("group") if current_map else None,
                "team_api_enabled": current_map.get("team_api_enabled") if current_map else False,
                "status": "active" if current_map and current_map.get("map_id") == map_id else "inactive"
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get map status for {map_id}: {e}")
            return {
                "map_id": map_id,
                "status": "error",
                "error": str(e)
            }

    def sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from configuration.

        Args:
            config: Configuration data

        Returns:
            dict: Sanitized configuration
        """
        try:
            sanitized = config.copy()

            # Remove sensitive MQTT data
            if "mqtt" in sanitized:
                sanitized["mqtt"] = sanitized["mqtt"].copy()
                sanitized["mqtt"]["password"] = "***"

            # Remove sensitive CalTopo data
            if "caltopo" in sanitized:
                sanitized["caltopo"] = sanitized["caltopo"].copy()
                if "team_api" in sanitized["caltopo"]:
                    sanitized["caltopo"]["team_api"] = sanitized["caltopo"]["team_api"].copy()
                    sanitized["caltopo"]["team_api"]["secret_key"] = "***"
                if "oauth" in sanitized["caltopo"]:
                    sanitized["caltopo"]["oauth"] = sanitized["caltopo"]["oauth"].copy()
                    sanitized["caltopo"]["oauth"]["client_secret"] = "***"

            # Remove sensitive Web UI data
            if "web_ui" in sanitized:
                sanitized["web_ui"] = sanitized["web_ui"].copy()
                sanitized["web_ui"]["secret_key"] = "***"

            return sanitized

        except Exception as e:
            logger.error(f"Failed to sanitize configuration: {e}")
            return config
