import pytest
from unittest.mock import Mock, AsyncMock

from mqtt_client import MqttClient

@pytest.fixture
def mock_config():
    config = Mock()
    config.mqtt.broker = "localhost"
    config.mqtt.port = 1883
    config.mqtt.username = "testuser"
    config.mqtt.password = Mock()
    config.mqtt.password.get_secret_value.return_value = "testpass"
    config.mqtt.topic = "test/topic"
    return config

@pytest.fixture
def message_callback():
    return AsyncMock()

@pytest.fixture
def client(mock_config, message_callback):
    import logging
    logging.getLogger("mqtt_client").setLevel(logging.CRITICAL)
    return MqttClient(mock_config, message_callback)

@pytest.mark.asyncio
async def test_protobuf_deduplication(client, message_callback):
    # Setup test message that is protobuf
    message_proto = Mock()
    message_proto.payload = b"fake"
    message_proto.topic = "msh/US/2/c/LongFast/!123"
    message_proto.retain = False

    # Setup test message that is JSON
    message_json = Mock()
    message_json.payload = b'{"from": 123, "type": "position"}'
    message_json.topic = "msh/US/2/json/LongFast/!123"
    message_json.retain = False

    # Send JSON
    await client._process_message(message_json)

    # Send protobuf
    await client._process_message(message_proto)

    # Send another protobuf for different node
    message_proto.topic = "msh/US/2/c/LongFast/!456"
    await client._process_message(message_proto)

    assert client.message_callback.call_count == 2
