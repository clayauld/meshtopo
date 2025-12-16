from unittest.mock import mock_open, patch

import pytest
import yaml

from config.config import CalTopoConfig, Config, LoggingConfig, MqttConfig, NodeMapping


class TestConfigMethods:
    def test_get_node_device_id(self):
        """Test get_node_device_id method."""
        config = Config(
            mqtt=MqttConfig(broker="test"),
            caltopo=CalTopoConfig(connect_key="test"),
            logging=LoggingConfig(),
            nodes={
                "!1234": NodeMapping(device_id="TEST-DEV", group="TEST-GROUP"),
                "!5678": NodeMapping(device_id="OTHER-DEV"),
            },
        )

        assert config.get_node_device_id("!1234") == "TEST-DEV"
        assert config.get_node_device_id("!5678") == "OTHER-DEV"
        assert config.get_node_device_id("!9999") is None

    def test_get_node_group(self):
        """Test get_node_group method."""
        config = Config(
            mqtt=MqttConfig(broker="test"),
            caltopo=CalTopoConfig(connect_key="test"),
            logging=LoggingConfig(),
            nodes={
                "!1234": NodeMapping(device_id="TEST-DEV", group="TEST-GROUP"),
                "!5678": NodeMapping(device_id="OTHER-DEV"),
            },
        )
        # Mock global group
        config.caltopo.group = "GLOBAL-GROUP"

        assert config.get_node_group("!1234") == "TEST-GROUP"
        assert config.get_node_group("!5678") == "GLOBAL-GROUP"
        assert config.get_node_group("!9999") == "GLOBAL-GROUP"

    def test_from_file_yaml_error(self):
        """Test loading config with invalid YAML."""
        with (
            patch("builtins.open", mock_open(read_data="invalid: yaml: :")),
            patch("pathlib.Path.exists", return_value=True),
        ):

            with pytest.raises(yaml.YAMLError):
                Config.from_file("config.yaml")

    def test_from_file_type_error(self):
        """Test loading config that is a list, not a dict."""
        with (
            patch("builtins.open", mock_open(read_data="- list item\n- another item")),
            patch("pathlib.Path.exists", return_value=True),
        ):

            with pytest.raises(TypeError, match="must be a dictionary"):
                Config.from_file("config.yaml")
