"""
Test CalTopo configuration modes - connect_key, group, and both modes support.
"""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from config.config import Config


class TestCalTopoModes:
    """Test CalTopo configuration modes."""

    def create_config_file(
        self, caltopo_config: dict, missing_logging: bool = False
    ) -> str:
        """Create a temporary config file with the given CalTopo configuration."""
        config_data = {
            "mqtt": {
                "broker": "test.mqtt.com",
                "port": 1883,
                "username": "test",
                "password": "test",
                "topic": "test/topic",
            },
            "caltopo": caltopo_config,
            "nodes": {"node1": {"device_id": "device123"}},
        }
        if not missing_logging:
            config_data["logging"] = {"level": "INFO"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            return f.name

    def test_connect_key_only_valid(self) -> None:
        """Test valid configuration with only connect_key."""
        config_path = self.create_config_file({"connect_key": "valid_key"})
        try:
            config = Config.from_file(config_path)

            assert config.caltopo.connect_key == "valid_key"
            assert config.caltopo.group is None
        finally:
            Path(config_path).unlink()

    def test_group_only_valid(self) -> None:
        """Test valid configuration with only group."""
        config_path = self.create_config_file({"group": "valid_group"})
        try:
            config = Config.from_file(config_path)

            assert config.caltopo.connect_key is None
            assert config.caltopo.group == "valid_group"
        finally:
            Path(config_path).unlink()

    def test_both_modes_valid(self) -> None:
        """Test valid configuration with both connect_key and group."""
        config_path = self.create_config_file(
            {"connect_key": "valid_key", "group": "valid_group"}
        )
        try:
            config = Config.from_file(config_path)

            assert config.caltopo.connect_key == "valid_key"
            assert config.caltopo.group == "valid_group"
        finally:
            Path(config_path).unlink()

    def test_no_modes_fails(self) -> None:
        """Test that configuration with no modes fails."""
        config_path = self.create_config_file({}, missing_logging=True)
        try:
            with pytest.raises(ValidationError):
                Config.from_file(config_path)
        finally:
            Path(config_path).unlink()

    def test_none_values_fail(self) -> None:
        """Test that None values for both fields fail."""
        config_path = self.create_config_file({"connect_key": None, "group": None})
        try:
            with pytest.raises(ValidationError):
                Config.from_file(config_path)
        finally:
            Path(config_path).unlink()

    def test_missing_caltopo_section_fails(self) -> None:
        """Test that missing caltopo section fails."""
        config_data = {
            "mqtt": {
                "broker": "test.mqtt.com",
                "port": 1883,
                "username": "test",
                "password": "test",
                "topic": "test/topic",
            },
            "nodes": {"node1": {"device_id": "device123"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            with pytest.raises(ValidationError):
                Config.from_file(config_path)
        finally:
            Path(config_path).unlink()
