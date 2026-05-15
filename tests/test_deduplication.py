from unittest.mock import AsyncMock, Mock, patch

import pytest

from gateway_app import GatewayApp


@pytest.fixture
def app():
    with patch("gateway_app.PersistentDict"):
        config = Mock()
        config.storage.db_path = ":memory:"
        app = GatewayApp(config)
        app.config = config
        app.logger = Mock()
        # Mock handlers to avoid side effects
        app._process_position_message = AsyncMock()
        app._process_nodeinfo_message = Mock()
        app._process_telemetry_message = Mock()
        app._process_traceroute_message = Mock()
        app._resolve_hardware_id = Mock(return_value="!123")
        return app


@pytest.mark.asyncio
async def test_gateway_app_deduplication(app):
    # Test JSON message
    msg1_json = {
        "from": 123,
        "type": "position",
        "id": 1001,
        "payload": {"latitude_i": 1, "longitude_i": 2},
    }

    # 1. Process msg1_json
    await app._process_message(msg1_json, "msh/US/2/json/LongFast/!123")
    assert app.stats["messages_processed"] == 1

    # 2. Process msg1_json again (duplicate)
    await app._process_message(msg1_json, "msh/US/2/json/LongFast/!123")
    assert app.stats["messages_received"] == 2
    assert app.stats["messages_processed"] == 1  # Still 1

    # 3. Process msg2_json (different packet ID, same node)
    msg2_json = msg1_json.copy()
    msg2_json["id"] = 1002
    await app._process_message(msg2_json, "msh/US/2/json/LongFast/!123")
    assert app.stats["messages_processed"] == 2  # Incremented!

    # 4. Process Protobuf (mocking packet extraction)
    with (patch("gateway_app.mqtt_pb2.ServiceEnvelope") as MockEnvelope,):
        mock_env = MockEnvelope.return_value
        mock_env.packet.id = 1002  # Same as msg2_json
        setattr(mock_env.packet, "from", 123)

        await app._process_protobuf_message(
            {"payload_bytes": b"proto"}, "topic", "channel"
        )
        assert (
            app.stats["messages_processed"] == 2
        )  # Still 2, because 1002 was already processed as JSON

        mock_env.packet.id = 1003  # New packet
        setattr(mock_env.packet, "from", 123)
        mock_env.packet.HasField.return_value = False
        await app._process_protobuf_message(
            {"payload_bytes": b"proto"}, "topic", "channel"
        )
        assert "123/1003" in app._current_messages
