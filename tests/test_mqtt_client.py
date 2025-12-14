import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import asyncio_mqtt as aiomqtt
import pytest

from mqtt_client import MqttClient


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
    async def test_run_success(self, client, message_callback):
        # Import mqtt_client to access its mqtt module
        import mqtt_client

        # Mock aiomqtt Client context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None

        # Mock messages iterator using a queue
        incoming_messages = asyncio.Queue()
        mock_msg = Mock(spec=aiomqtt.Message)
        mock_msg.payload = b'{"test": 1}'
        # aiomqtt messages have a topic object with a value attribute
        mock_msg.topic = Mock()
        mock_msg.topic.value = "test/topic"

        # Create an async iterable for messages
        class AsyncMessages:
            def __aiter__(self):
                return self

            async def __anext__(self):
                return await incoming_messages.get()

        mock_client_instance.messages = AsyncMessages()

        # Mock the aiomqtt.Client class to return our
        # mock_client_instance when instantiated
        with patch.object(
            mqtt_client.mqtt,
            "Client",
            new=Mock(return_value=mock_client_instance),
        ):
            # Run the client in a background task
            run_task = asyncio.create_task(client.run())

            # Give the client a moment to connect and subscribe
            await asyncio.sleep(0.1)

            # Put a message into the queue for the client to process
            await incoming_messages.put(mock_msg)

            # Wait for the callback to be called
            await asyncio.sleep(0.1)

            # Cancel the client task
            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass

        # Verify interactions
        mock_client_instance.subscribe.assert_called_once_with("test/topic")
        message_callback.assert_called_once_with({"test": 1})

    @pytest.mark.asyncio
    async def test_run_connection_failure_retry(self, client):
        # Import mqtt_client to access its mqtt module
        import mqtt_client

        # Simulate connection failure then success
        mock_client_instance = AsyncMock()

        # Track connection attempts
        call_count = 0

        async def side_effect_enter():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiomqtt.MqttError("Connection failed")
            return mock_client_instance

        mock_client_instance.__aenter__.side_effect = side_effect_enter
        mock_client_instance.__aexit__.return_value = None

        # Create an async iterable for messages that hangs
        class AsyncMessages:
            def __aiter__(self):
                return self

            async def __anext__(self):
                # Hang forever until canceled
                await asyncio.Event().wait()

        mock_client_instance.messages = AsyncMessages()

        with patch.object(
            mqtt_client.mqtt,
            "Client",
            new=Mock(return_value=mock_client_instance),
        ):
            # Run the client in a background task
            run_task = asyncio.create_task(client.run())

            # Wait for connection failure and retry
            # First attempt fails, sleeps for 1 second, then retries
            await asyncio.sleep(1.5)

            # Cancel the client task to stop the infinite loop
            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass

        # Should have attempted connection twice
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_process_message_valid(self, client):
        message = Mock()
        message.payload = b'{"key": "value"}'
        # aiomqtt topic is an object with value attribute
        message.topic.value = "test/topic"

        await client._process_message(message)

        client.message_callback.assert_called_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, client):
        message = Mock()
        message.payload = b"invalid json"

        await client._process_message(message)

        client.message_callback.assert_not_called()
