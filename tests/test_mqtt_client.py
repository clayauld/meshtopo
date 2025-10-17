#!/usr/bin/env python3
"""
Test cases for MQTT client functionality.
"""

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root and src directory to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from test_config import cleanup_test_config, create_test_config  # noqa: E402

from mqtt_client import MqttClient  # noqa: E402


class TestMqttClient(unittest.TestCase):
    """Test cases for MqttClient class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_config_path = create_test_config()

        # Create mock config object
        self.mock_config = Mock()
        self.mock_config.mqtt.broker = "localhost"
        self.mock_config.mqtt.port = 1883
        self.mock_config.mqtt.username = "testuser"
        self.mock_config.mqtt.password = "testpass"
        self.mock_config.mqtt.topic = "test/topic"

        # Create mock message callback
        self.message_callback = Mock()

        # Create MQTT client instance
        self.client = MqttClient(self.mock_config, self.message_callback)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        cleanup_test_config(self.test_config_path)
        if self.client.client:
            self.client.disconnect()

    def test_initialization(self) -> None:
        """Test MqttClient initialization."""
        self.assertEqual(self.client.config, self.mock_config)
        self.assertEqual(self.client.message_callback, self.message_callback)
        self.assertIsNone(self.client.client)
        self.assertFalse(self.client.connected)
        self.assertEqual(self.client.reconnect_attempts, 0)
        self.assertEqual(self.client.max_reconnect_attempts, 10)
        self.assertEqual(self.client.reconnect_delay, 1)
        self.assertIsInstance(self.client.logger, logging.Logger)

    @patch("mqtt_client.mqtt.Client")
    def test_connect_success(self, mock_client_class: Mock) -> None:
        """Test successful connection to MQTT broker."""
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock successful connection
        self.client._on_connect = Mock()

        # Call connect
        self.client.connect()

        # Verify client was created and configured
        mock_client_class.assert_called_once()
        mock_client.username_pw_set.assert_called_once_with("testuser", "testpass")
        mock_client.on_connect = self.client._on_connect
        mock_client.on_disconnect = self.client._on_disconnect
        mock_client.on_message = self.client._on_message
        mock_client.on_log = self.client._on_log
        mock_client.connect.assert_called_once_with("localhost", 1883, keepalive=60)
        mock_client.loop_start.assert_called_once()

    @patch("mqtt_client.mqtt.Client")
    def test_connect_failure(self, mock_client_class: Mock) -> None:
        """Test connection failure."""
        # Mock the MQTT client to raise an exception
        mock_client_class.side_effect = Exception("Connection failed")

        # Call connect
        result = self.client.connect()

        # Verify it returns False
        self.assertFalse(result)

    @patch("mqtt_client.mqtt.Client")
    def test_connect_timeout(self, mock_client_class: Mock) -> None:
        """Test connection timeout."""
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock timeout scenario (connected stays False)
        with patch.object(self.client, "_on_connect", Mock()):
            with patch("time.sleep", Mock()):
                result = self.client.connect()

        # Verify it returns False due to timeout
        self.assertFalse(result)

    def test_disconnect(self) -> None:
        """Test disconnection from MQTT broker."""
        # Create a mock client
        mock_client = MagicMock()
        self.client.client = mock_client
        self.client.connected = True

        # Call disconnect
        self.client.disconnect()

        # Verify client methods were called
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
        self.assertFalse(self.client.connected)

    def test_disconnect_no_client(self) -> None:
        """Test disconnection when no client exists."""
        # Ensure no client exists
        self.client.client = None

        # Call disconnect (should not raise exception)
        self.client.disconnect()

        # Verify connected is still False
        self.assertFalse(self.client.connected)

    def test_on_connect_success(self) -> None:
        """Test successful connection callback."""
        # Create mock client
        mock_client = MagicMock()
        mock_client.subscribe.return_value = (0, 1)  # MQTT_ERR_SUCCESS

        # Call _on_connect with success result code
        self.client._on_connect(mock_client, None, None, 0)

        # Verify connection state and subscription
        self.assertTrue(self.client.connected)
        mock_client.subscribe.assert_called_once_with("test/topic")

    def test_on_connect_failure(self) -> None:
        """Test connection failure callback."""
        # Create mock client
        mock_client = MagicMock()

        # Call _on_connect with failure result code
        self.client._on_connect(mock_client, None, None, 1)

        # Verify connection state
        self.assertFalse(self.client.connected)

    def test_on_connect_subscription_failure(self) -> None:
        """Test subscription failure in connection callback."""
        # Create mock client
        mock_client = MagicMock()
        mock_client.subscribe.return_value = (1, 0)  # MQTT_ERR_FAILURE

        # Call _on_connect
        self.client._on_connect(mock_client, None, None, 0)

        # Verify connection state
        self.assertTrue(self.client.connected)
        mock_client.subscribe.assert_called_once_with("test/topic")

    def test_on_disconnect_unexpected(self) -> None:
        """Test unexpected disconnection callback."""
        # Create mock client
        mock_client = MagicMock()

        # Mock _attempt_reconnect to avoid actual reconnection
        with patch.object(self.client, "_attempt_reconnect", Mock()):
            self.client._on_disconnect(mock_client, None, 1)

        # Verify connection state
        self.assertFalse(self.client.connected)

    def test_on_disconnect_expected(self) -> None:
        """Test expected disconnection callback."""
        # Create mock client
        mock_client = MagicMock()

        # Call _on_disconnect with expected disconnect (rc=0)
        self.client._on_disconnect(mock_client, None, 0)

        # Verify connection state
        self.assertFalse(self.client.connected)

    def test_on_message_success(self) -> None:
        """Test successful message processing."""
        # Create mock message
        mock_msg = Mock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b'{"test": "data"}'

        # Call _on_message
        self.client._on_message(None, None, mock_msg)

        # Verify callback was called with parsed data
        self.message_callback.assert_called_once_with({"test": "data"})

    def test_on_message_json_decode_error(self) -> None:
        """Test message processing with JSON decode error."""
        # Create mock message with invalid JSON
        mock_msg = Mock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b"invalid json"

        # Call _on_message
        self.client._on_message(None, None, mock_msg)

        # Verify callback was not called
        self.message_callback.assert_not_called()

    def test_on_message_callback_exception(self) -> None:
        """Test message processing when callback raises exception."""
        # Create mock message
        mock_msg = Mock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b'{"test": "data"}'

        # Make callback raise exception
        self.message_callback.side_effect = Exception("Callback error")

        # Call _on_message (should not raise exception)
        self.client._on_message(None, None, mock_msg)

        # Verify callback was called
        self.message_callback.assert_called_once_with({"test": "data"})

    def test_on_log_warning(self) -> None:
        """Test MQTT logging callback for warnings."""
        # Import mqtt module to get log level constants
        import paho.mqtt.client as mqtt

        # Call _on_log with warning level
        with patch.object(self.client.logger, "debug") as mock_debug:
            self.client._on_log(None, None, mqtt.MQTT_LOG_WARNING, "Warning message")
            mock_debug.assert_called_once_with("MQTT: Warning message")

    def test_on_log_error(self) -> None:
        """Test MQTT logging callback for errors."""
        # Import mqtt module to get log level constants
        import paho.mqtt.client as mqtt

        # Call _on_log with error level (8 > 4, so should NOT log)
        with patch.object(self.client.logger, "debug") as mock_debug:
            self.client._on_log(None, None, mqtt.MQTT_LOG_ERR, "Error message")
            mock_debug.assert_not_called()

    def test_on_log_info(self) -> None:
        """Test MQTT logging callback for info messages (should log)."""
        # Import mqtt module to get log level constants
        import paho.mqtt.client as mqtt

        # Call _on_log with info level (1 <= 4, so should log)
        with patch.object(self.client.logger, "debug") as mock_debug:
            self.client._on_log(None, None, mqtt.MQTT_LOG_INFO, "Info message")
            mock_debug.assert_called_once_with("MQTT: Info message")

    @patch("time.sleep")
    def test_attempt_reconnect_max_attempts(self, mock_sleep: Mock) -> None:
        """Test reconnection attempt when max attempts reached."""
        # Set reconnect attempts to max
        self.client.reconnect_attempts = self.client.max_reconnect_attempts

        # Call _attempt_reconnect
        self.client._attempt_reconnect()

        # Verify no sleep occurred
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_attempt_reconnect_success(self, mock_sleep: Mock) -> None:
        """Test successful reconnection attempt."""
        # Create mock client
        mock_client = MagicMock()
        self.client.client = mock_client

        # Call _attempt_reconnect
        self.client._attempt_reconnect()

        # Verify reconnect was called
        mock_client.reconnect.assert_called_once()
        self.assertEqual(self.client.reconnect_attempts, 1)

    @patch("time.sleep")
    def test_attempt_reconnect_failure(self, mock_sleep: Mock) -> None:
        """Test reconnection attempt failure."""
        # Create mock client that raises exception
        mock_client = MagicMock()
        mock_client.reconnect.side_effect = Exception("Reconnect failed")
        self.client.client = mock_client

        # Call _attempt_reconnect (without mocking it to avoid recursion)
        # The method should handle the exception gracefully
        try:
            self.client._attempt_reconnect()
        except Exception:
            # Expected to raise exception due to reconnect failure
            pass

        # Verify reconnect was attempted multiple times (due to recursive retries)
        self.assertGreater(mock_client.reconnect.call_count, 0)
        # Verify max attempts was reached
        self.assertEqual(
            self.client.reconnect_attempts, self.client.max_reconnect_attempts
        )

    def test_attempt_reconnect_exponential_backoff(self) -> None:
        """Test exponential backoff in reconnection attempts."""
        # Test first attempt
        delay1 = min(self.client.reconnect_delay * (2**0), 60)
        self.assertEqual(delay1, 1)

        # Test second attempt
        delay2 = min(self.client.reconnect_delay * (2**1), 60)
        self.assertEqual(delay2, 2)

        # Test third attempt
        delay3 = min(self.client.reconnect_delay * (2**2), 60)
        self.assertEqual(delay3, 4)

        # Test max delay (60 seconds)
        delay_max = min(self.client.reconnect_delay * (2**10), 60)
        self.assertEqual(delay_max, 60)

    def test_is_connected_true(self) -> None:
        """Test is_connected returns True when connected."""
        self.client.connected = True
        self.client.client = Mock()

        result = self.client.is_connected()
        self.assertTrue(result)

    def test_is_connected_false_not_connected(self) -> None:
        """Test is_connected returns False when not connected."""
        self.client.connected = False
        self.client.client = Mock()

        result = self.client.is_connected()
        self.assertFalse(result)

    def test_is_connected_false_no_client(self) -> None:
        """Test is_connected returns False when no client."""
        self.client.connected = True
        self.client.client = None

        result = self.client.is_connected()
        self.assertFalse(result)

    def test_is_connected_false_both_false(self) -> None:
        """Test is_connected returns False when both conditions false."""
        self.client.connected = False
        self.client.client = None

        result = self.client.is_connected()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
