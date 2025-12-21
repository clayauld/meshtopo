import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from gateway_app import GatewayApp


@pytest.fixture
def mock_config():
    config = Mock()
    config.mqtt.use_internal_broker = False
    config.mqtt.broker = "mqtt.example.com"
    config.nodes = {"!823a4edc": {"device_id": "TEAM-LEAD"}}
    config.get_node_device_id.side_effect = lambda x: {"!823a4edc": "TEAM-LEAD"}.get(x)
    config.devices.allow_unknown_devices = False
    config.caltopo.group = None
    config.caltopo.has_group = False
    config.caltopo.connect_key = "key"
    config.caltopo.has_connect_key = True
    config.storage.db_path = "test_db.sqlite"
    return config


class MockPersistentDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def close(self):
        pass


@pytest.fixture
def app(mock_config):
    with (
        patch("gateway_app.Config") as MockConfig,
        patch("gateway_app.PersistentDict") as MockPersistentDictClass,
    ):

        MockConfig.from_file.return_value = mock_config

        # Setup MockPersistentDict behavior
        mock_db_instance = MockPersistentDict()
        MockPersistentDictClass.return_value = mock_db_instance

        app = GatewayApp("dummy_config.yaml")
        app.config = mock_config
        # We start with plain dicts, but the code checks isinstance
        # against the class we patched
        app.node_id_mapping = mock_db_instance
        app.callsign_mapping = mock_db_instance

        # Attach for testing
        app._MockPersistentDictClass = MockPersistentDictClass

        yield app


class TestGatewayApp:
    def test_init(self):
        app = GatewayApp("config.yaml")
        assert app.config_path == "config.yaml"
        assert app.stop_event is None
        assert app.stats["messages_received"] == 0

    @patch("gateway_app.MqttClient")
    @patch("gateway_app.CalTopoReporter")
    @pytest.mark.asyncio
    async def test_initialize_success(self, MockReporter, MockMqtt, app):
        app.config.setup_logging = Mock()

        # Mock Reporter
        mock_reporter_instance = MockReporter.return_value
        mock_reporter_instance.test_connection = AsyncMock(return_value=True)
        mock_reporter_instance.start = AsyncMock()

        # Mock Mqtt Client
        MockMqtt.return_value = Mock()  # The init is sync

        assert await app.initialize() is True

        assert app.mqtt_client is not None
        assert app.caltopo_reporter is not None
        assert "!823a4edc" in app.configured_devices

        # Verify DB initialization with configured path in MockPersistentDict
        # The PersistentDict constructor should have been called with our test path
        app._MockPersistentDictClass.assert_any_call(
            "test_db.sqlite",
            tablename="node_id_mapping",
            autocommit=True,
        )

    @pytest.mark.asyncio
    async def test_initialize_failure(self, app):
        with patch(
            "gateway_app.Config.from_file",
            side_effect=Exception("Config Error"),
        ):
            assert await app.initialize() is False

    @patch("gateway_app.sys.exit")
    @pytest.mark.asyncio
    async def test_start_success(self, mock_exit, app):
        app.initialize = AsyncMock(return_value=True)
        app.mqtt_client = Mock()
        app.mqtt_client.run = AsyncMock()  # run is async

        # We need to simulate the stop event being set eventually so start returns
        async def trigger_stop():
            await asyncio.sleep(0.1)
            app.stop_event.set()

        asyncio.create_task(trigger_stop())

        # Start should wait until stop_event is set
        await app.start()

        assert app.mqtt_client.run.called
        # Should call stats loop too, but that's internal async task

    @patch("gateway_app.sys.exit")
    @pytest.mark.asyncio
    async def test_start_init_failure(self, mock_exit, app):
        app.initialize = AsyncMock(return_value=False)
        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            await app.start()
        mock_exit.assert_called_with(1)

    @patch("gateway_app.sys.exit")
    @pytest.mark.asyncio
    async def test_start_mqtt_not_init(self, mock_exit, app):
        app.initialize = AsyncMock(return_value=True)
        app.mqtt_client = None  # Not initialized
        mock_exit.side_effect = SystemExit

        with pytest.raises(SystemExit):
            await app.start()
        mock_exit.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_stop(self, app):
        app.mqtt_client = Mock()
        app.caltopo_reporter = AsyncMock()  # async close
        app.stop_event = asyncio.Event()

        await app.stop()

        assert app.stop_event.is_set()
        assert app.caltopo_reporter.close.called
        # Database close called via app.close()

    @pytest.mark.asyncio
    async def test_process_message_no_type(self, app):
        # Should just return/log warning
        await app._process_message({"from": 123})
        assert app.stats["messages_received"] == 1
        assert app.stats["messages_processed"] == 0

    @pytest.mark.asyncio
    async def test_process_message_unknown_type(self, app):
        await app._process_message({"from": 123, "type": "unknown"})
        assert app.stats["messages_received"] == 1
        assert app.stats["messages_processed"] == 0

    def test_process_nodeinfo_message(self, app):
        # nodeinfo is still sync internal method, but called from async
        msg = {
            "from": 123,
            "type": "nodeinfo",
            "payload": {
                "id": "!823a4edc",
                "longname": "Test Node",
                "shortname": "TEST",
            },
        }
        app._process_nodeinfo_message(msg, "123")

        assert app.node_id_mapping["123"] == "!823a4edc"
        # Should use configured name
        assert app.callsign_mapping["!823a4edc"] == "TEAM-LEAD"

    def test_process_nodeinfo_fallback_names(self, app):
        # Case 1: Longname fallback
        app.config.get_node_device_id.return_value = None
        msg = {
            "from": 456,
            "type": "nodeinfo",
            "payload": {"id": "!unknown", "longname": "Long Name"},
        }
        app._process_nodeinfo_message(msg, "456")
        assert app.callsign_mapping["!unknown"] == "Long Name"

        # Case 2: Shortname fallback
        msg["payload"] = {"id": "!unknown2", "shortname": "Short"}
        app._process_nodeinfo_message(msg, "789")
        assert app.callsign_mapping["!unknown2"] == "Short"

    @pytest.mark.asyncio
    async def test_process_position_message_success(self, app):
        app.caltopo_reporter = Mock()
        # send_position_update is async
        app.caltopo_reporter.send_position_update = AsyncMock(return_value=True)
        app.node_id_mapping["123"] = "!823a4edc"
        app._node_id_cache["123"] = "!823a4edc"
        app.callsign_mapping["!823a4edc"] = "TEAM-LEAD"
        app._callsign_cache["!823a4edc"] = "TEAM-LEAD"

        msg = {
            "type": "position",
            "payload": {"latitude_i": 100000000, "longitude_i": 200000000},
        }

        await app._process_position_message(msg, "123")

        app.caltopo_reporter.send_position_update.assert_called_with(
            "TEAM-LEAD", 10.0, 20.0, None
        )
        assert app.stats["position_updates_sent"] == 1

    @pytest.mark.asyncio
    async def test_process_position_message_no_payload(self, app):
        app.caltopo_reporter = Mock()
        app.caltopo_reporter.send_position_update = AsyncMock()
        await app._process_position_message({}, "123")
        app.caltopo_reporter.send_position_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_position_deterministic_id(self, app):
        app.caltopo_reporter = Mock()
        app.caltopo_reporter.send_position_update = AsyncMock(return_value=True)
        # Allow unknown devices so the new deterministic ID is accepted
        app.config.devices.allow_unknown_devices = True

        # Not in mapping, sender field ignored
        msg = {
            "type": "position",
            "sender": "!823a4edc",  # Should be ignored now
            "payload": {"latitude_i": 100000000, "longitude_i": 200000000},
        }

        # 123 -> !0000007b
        await app._process_position_message(msg, "123")

        assert app.node_id_mapping["123"] == "!0000007b"
        app.caltopo_reporter.send_position_update.assert_called()

    @pytest.mark.asyncio
    async def test_process_position_unknown_device_blocked(self, app):
        app.caltopo_reporter = Mock()
        app.caltopo_reporter.send_position_update = AsyncMock()
        app.config.devices.allow_unknown_devices = False
        app.configured_devices = set(["!known"])
        app.node_id_mapping["999"] = "!unknown"

        msg = {
            "type": "position",
            "payload": {"latitude_i": 100, "longitude_i": 200},
        }
        await app._process_position_message(msg, "999")

        app.caltopo_reporter.send_position_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_position_unknown_device_allowed(self, app) -> None:
        app.caltopo_reporter = Mock()
        app.caltopo_reporter.send_position_update = AsyncMock(return_value=True)
        app.config.devices.allow_unknown_devices = True
        app.configured_devices = set(["!known"])
        app.node_id_mapping["999"] = "!unknown"
        app._node_id_cache["999"] = "!unknown"

        msg = {
            "type": "position",
            "payload": {"latitude_i": 100, "longitude_i": 200},
        }
        await app._process_position_message(msg, "999")

        app.caltopo_reporter.send_position_update.assert_called_with(
            "!unknown", 0.00001, 0.00002, None
        )

    def test_telemetry_message(self, app):
        msg = {"type": "telemetry", "payload": {"battery_level": 100}}
        # Just ensure no exception
        app._process_telemetry_message(msg, "123")

    def test_traceroute_message(self, app):
        msg = {"type": "traceroute", "payload": {"route": []}}
        # Just ensure no exception
        app._process_traceroute_message(msg, "123")

    @pytest.mark.asyncio
    async def test_db_directory_creation_failure(self, mock_config):
        """Test error handling when creating database directory fails."""
        with (
            patch("gateway_app.Config") as MockConfig,
            patch("gateway_app.PersistentDict"),
            patch("gateway_app.os.makedirs", side_effect=OSError("Permission denied")),
            patch("gateway_app.os.path.dirname", return_value="/protected/dir"),
        ):
            MockConfig.from_file.return_value = mock_config
            app = GatewayApp("dummy_config.yaml")

            # This should log an error but not raise exception (fail open/continue)
            # The code catches OSError
            await app.initialize()

            # Verify we tried to create dir
            import gateway_app

            gateway_app.os.makedirs.assert_called_once()

    @pytest.mark.asyncio
    async def test_caltopo_connection_fail_continue(self, mock_config):
        """Test that initialization continues even if CalTopo test fails."""
        with (
            patch("gateway_app.Config") as MockConfig,
            patch("gateway_app.PersistentDict"),
            patch("gateway_app.CalTopoReporter") as MockReporterClass,
            patch("gateway_app.MqttClient"),
        ):
            MockConfig.from_file.return_value = mock_config
            mock_reporter = MockReporterClass.return_value
            mock_reporter.test_connection = AsyncMock(return_value=False)
            mock_reporter.start = AsyncMock()

            app = GatewayApp("dummy_config.yaml")
            success = await app.initialize()

            assert success is True

    @pytest.mark.asyncio
    async def test_process_message_exceptions(self, app):
        """Test exception handling in message processing."""
        # Using app fixture for convenience, but resetting stats
        app.stats = {"messages_processed": 0, "errors": 0, "messages_received": 0}

        # 1. Empty message type
        await app._process_message({"type": "", "from": 123})
        assert app.stats["messages_processed"] == 0

        # 2. Unsupported message type
        await app._process_message({"type": "unknown_type", "from": 123})
        assert app.stats["messages_processed"] == 0

        # 3. Exception during processing (simulated by malformed data causing error)
        with patch.object(
            app, "_process_position_message", side_effect=ValueError("Boom")
        ):
            await app._process_message({"type": "position", "from": 123})
            assert app.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_stats_loop_cancellation(self, app):
        """Test that stats loop runs and handles cancellation."""
        app.stop_event = asyncio.Event()

        # Start stats loop task
        task = asyncio.create_task(app._stats_loop())

        # Let it run a bit
        await asyncio.sleep(0.1)
        app.stop_event.set()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
