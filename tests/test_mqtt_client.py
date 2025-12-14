import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import asyncio_mqtt as aiomqtt
import pytest

from mqtt_client import MqttClient


# Helper to make the iterator a context manager
class AsyncContextManagerIterator:
    def __init__(self, iterator):
        self.iterator = iterator

    async def __aenter__(self):
        return self.iterator

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.fixture
def mock_config():
    config = Mock()
    config.mqtt.broker = "localhost"
    config.mqtt.port = 1883
    config.mqtt.username = "testuser"
    config.mqtt.password = "testpass"
    config.mqtt.topic = "test/topic"
    return config


@pytest.fixture
def message_callback():
    return AsyncMock()


@pytest.fixture
def client(mock_config, message_callback):
    # Suppress logging
    logging.getLogger("mqtt_client").setLevel(logging.CRITICAL)
    return MqttClient(mock_config, message_callback)


class TestMqttClient:
    def test_initialization(self, client, mock_config, message_callback):
        assert client.config == mock_config
        assert client.message_callback == message_callback
        assert client.message_callback == message_callback

    @pytest.mark.asyncio
    async def test_run_success(self, client):
        # Mock aiomqtt Client context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None

        # Mock messages iterator
        mock_msg = Mock()
        mock_msg.payload = b'{"test": 1}'
        mock_msg.topic = "test/topic"

        # Setup iterator to yield one message then raise CancelledError (or just stop)
        # But run() loops forever on messages().
        # We can simulate the iterator yielding items.
        mock_client_instance.messages = Mock()

        async def message_iterator():
            yield mock_msg
            # Raise CancelledError to exit the run loop cleanly (simulating
            # cancellation)
            raise asyncio.CancelledError()

        mock_client_instance.messages.return_value = AsyncContextManagerIterator(
            message_iterator()
        )

        # Mock sleep to prevent waiting and allow breaking if loop continues
        mock_sleep = AsyncMock()
        mock_sleep.side_effect = asyncio.CancelledError("Force exit if looped")

        # Spy on _process_message
        with (
            patch("asyncio_mqtt.Client", return_value=mock_client_instance),
            patch("asyncio.sleep", mock_sleep),
            patch.object(
                client, "_process_message", wraps=client._process_message
            ) as mock_process,
        ):
            try:
                await client.run()
            except asyncio.CancelledError:
                pass

        print(f"Process message called: {mock_process.called}")
        if mock_process.called:
            print(f"Process message args: {mock_process.call_args}")

        # Verify interactions
        assert mock_client_instance.subscribe.called
        assert client.message_callback.called
        client.message_callback.assert_called_with({"test": 1})

    @pytest.mark.asyncio
    async def test_run_connection_failure_retry(self, client):
        # Simulate connection failure then success
        mock_client_instance = AsyncMock()

        # First attempt raises MqttError, second succeeds (and then we cancel)
        call_count = 0

        async def side_effect_enter():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiomqtt.MqttError("Connection failed")
            return mock_client_instance

        mock_client_instance.__aenter__.side_effect = side_effect_enter
        mock_client_instance.__aenter__.side_effect = side_effect_enter
        mock_client_instance.__aexit__.return_value = None

        # Fix: messages should not be an async mock that returns a coroutine
        mock_client_instance.messages = Mock()

        # Messages for successful connection
        async def message_iterator():
            if False:
                yield
            raise asyncio.CancelledError()  # Stop immediately after connect

        mock_client_instance.messages.return_value = AsyncContextManagerIterator(
            message_iterator()
        )

        # Mock sleep to speed up test
        with (
            patch("asyncio_mqtt.Client", return_value=mock_client_instance),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):

            try:
                await client.run()
            except asyncio.CancelledError:
                pass

        # Should have attempted connection twice
        assert call_count >= 2
        mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_process_message_valid(self, client):
        message = Mock()
        message.payload = b'{"key": "value"}'
        message.topic.value = "test/topic"  # aiomqtt topic is an object string-like

        await client._process_message(message)

        client.message_callback.assert_called_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, client):
        message = Mock()
        message.payload = b"invalid json"

        await client._process_message(message)

        client.message_callback.assert_not_called()
