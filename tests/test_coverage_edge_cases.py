import os
import json
import pytest
import asyncio
import logging
import importlib
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from gateway_app import GatewayApp
import caltopo_reporter
from caltopo_reporter import CalTopoReporter
from config.config import Config


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.storage = MagicMock()
    config.storage.db_path = "test_state.sqlite"
    config.mqtt = MagicMock()
    config.mqtt.use_internal_broker = False
    config.nodes = {}
    config.caltopo = MagicMock()
    config.caltopo.has_connect_key = True
    config.caltopo.connect_key = "test_key"
    config.caltopo.has_group = False
    config.caltopo.group = "test_group"
    return config


@pytest.mark.asyncio
async def test_convert_numeric_to_id_error_handling():
    app = GatewayApp()
    assert app._convert_numeric_to_id(24896776) == "!017be508"
    assert app._convert_numeric_to_id("24896776") == "!017be508"
    assert app._convert_numeric_to_id(None) == "!None"
    assert app._convert_numeric_to_id("not_a_number") == "!not_a_number"


@pytest.mark.asyncio
async def test_process_message_missing_from_field():
    app = GatewayApp()
    app.logger = MagicMock()
    data = {"type": "position", "payload": {}}
    await app._process_message(data)
    app.logger.warning.assert_called_with("Received message without from field")


@pytest.mark.asyncio
async def test_process_position_message_missing_coordinates(mock_config):
    app = GatewayApp()
    app.config = mock_config
    app.node_id_mapping = MagicMock()
    app.callsign_mapping = MagicMock()
    app.logger = MagicMock()

    # Check "without payload"
    await app._process_position_message({}, "123")
    app.logger.warning.assert_any_call(
        "Received position message from 123 without payload"
    )

    # Check "without coordinates" - need non-empty but invalid payload
    await app._process_position_message({"payload": {"something": "else"}}, "123")
    found = False
    for call in app.logger.warning.call_args_list:
        if "without coordinates" in str(call):
            found = True
            break
    assert found, f"Warning not found in {app.logger.warning.call_args_list}"


@pytest.mark.asyncio
async def test_process_position_message_retained(mock_config):
    app = GatewayApp()
    app.config = mock_config
    app.node_id_mapping = MagicMock()
    app.callsign_mapping = MagicMock()
    app.logger = MagicMock()

    data = {"_mqtt_retain": True}
    await app._process_position_message(data, "123")
    app.logger.info.assert_called_with("Skipping retained position message from 123")


@pytest.mark.asyncio
async def test_initialize_db_reset_on_failure(mock_config, tmp_path):
    db_file = tmp_path / "corrupt.sqlite"
    mock_config.storage.db_path = str(db_file)

    app = GatewayApp()
    with patch("gateway_app.Config.from_file", return_value=mock_config):
        with patch(
            "gateway_app.SqliteDict",
            side_effect=[Exception("Corrupt"), MagicMock(), MagicMock()],
        ):
            mock_reporter = MagicMock(spec=CalTopoReporter)
            mock_reporter.start = AsyncMock()
            mock_reporter.test_connection = AsyncMock(return_value=True)

            with patch("gateway_app.CalTopoReporter", return_value=mock_reporter):
                with patch("gateway_app.MqttClient"):
                    success = await app.initialize()
                    assert success is True
                    assert app.node_id_mapping is not None
                    app.close()


def test_caltopo_reporter_url_validation():
    with patch.dict(os.environ, {"CALTOPO_URL": "https://invalid.com"}, clear=True):
        with pytest.raises(
            ValueError, match="Hostname must be 'caltopo.com' or a subdomain thereof"
        ):
            importlib.reload(caltopo_reporter)
    with patch.dict(
        os.environ,
        {"CALTOPO_URL": "https://caltopo.com/api/v1/position/report"},
        clear=True,
    ):
        importlib.reload(caltopo_reporter)


@pytest.mark.asyncio
async def test_telemetry_traceroute_missing_payload():
    app = GatewayApp()
    app.logger = MagicMock()
    app._process_telemetry_message({}, "123")
    assert any("without payload" in str(c) for c in app.logger.warning.call_args_list)
    app.logger.reset_mock()
    app._process_traceroute_message({}, "123")
    assert any("without payload" in str(c) for c in app.logger.warning.call_args_list)


@pytest.mark.asyncio
async def test_gateway_app_initialization_directory_creation_failure(mock_config):
    app = GatewayApp()
    app.logger = MagicMock()
    # Ensure there is a directory component
    mock_config.storage.db_path = "some_dir/test_state.sqlite"

    with patch("gateway_app.Config.from_file", return_value=mock_config):
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            mock_reporter = MagicMock(spec=CalTopoReporter)
            mock_reporter.start = AsyncMock()
            mock_reporter.test_connection = AsyncMock(return_value=True)
            with (
                patch("gateway_app.SqliteDict"),
                patch("gateway_app.CalTopoReporter", return_value=mock_reporter),
                patch("gateway_app.MqttClient"),
                patch("gateway_app.os.path.exists", return_value=False),
            ):
                await app.initialize()
                assert app.logger.error.called
