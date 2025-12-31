"""
AsyncIO MQTT Client Wrapper

This module provides a robust wrapper around `aiomqtt` (which wraps `paho-mqtt`)
to handle connection management, subscription, and message dispatch.

## Features

*   **Automatic Reconnection:** Implements an infinite loop with exponential backoff
    to handle broker disconnections and network instability.
*   **Async Stream:** Consumes messages from `aiomqtt.Client.messages` async generator.
*   **Security:** Handles authentication via username/password (from `SecretStr`).

## Usage

Instantiate `MqttClient` with a configuration object and a callback function.
Then, `await client.run()` to start the connection loop. This method blocks
until cancelled.
"""

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import aiomqtt as mqtt

from utils import sanitize_for_log


class MqttClient:
    """
    Manages the MQTT connection life-cycle.
    """

    def __init__(
        self,
        config: Any,
        message_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
        Initialize MQTT client.

        Args:
            config: Configuration object containing MQTT settings (broker, port, etc.)
            message_callback: Async function to call when a valid JSON message is received.
        """
        self.config = config
        self.message_callback = message_callback
        self.client: Optional[mqtt.Client] = None
        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        """
        Main connection loop.

        Connects to the broker, subscribes to topics, and processes messages.
        If the connection drops, it catches the `MqttError`, waits, and retries.

        The backoff strategy starts at 1s and doubles up to 60s.
        """
        reconnect_interval = 1
        max_reconnect_interval = 60

        while True:
            try:
                self.logger.info(
                    f"Connecting to MQTT broker at "
                    f"{self.config.mqtt.broker}: {self.config.mqtt.port}"
                )
                async with mqtt.Client(
                    hostname=self.config.mqtt.broker,
                    port=self.config.mqtt.port,
                    username=self.config.mqtt.username,
                    password=self.config.mqtt.password.get_secret_value(),
                    keepalive=60,
                ) as client:
                    self.client = client
                    self.logger.info("Connected to MQTT broker")
                    reconnect_interval = 1  # Reset backoff on successful connection

                    topic = self.config.mqtt.topic
                    await client.subscribe(topic)
                    self.logger.info(f"Subscribed to topic: {topic}")

                    async for message in client.messages:
                        await self._process_message(message)

            except mqtt.MqttError as e:
                self.logger.error(f"MQTT error: {e}")
            except asyncio.CancelledError:
                # Allow clean cancellation from parent task
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error in MQTT client: {e}")
            finally:
                self.logger.info("Disconnected from MQTT broker")
                self.client = None

            # Exponential backoff
            self.logger.info(f"Reconnecting in {reconnect_interval} seconds...")
            await asyncio.sleep(reconnect_interval)
            reconnect_interval = min(reconnect_interval * 2, max_reconnect_interval)

    async def _process_message(self, message: Any) -> None:
        """
        Internal message handler.

        1. Decodes payload (UTF-8).
        2. Logs (sanitized).
        3. Parses JSON.
        4. Injects `_mqtt_retain` flag.
        5. Awaits the callback.
        """
        try:
            payload = message.payload.decode("utf-8")
            self.logger.debug(
                f"Received message on topic {sanitize_for_log(message.topic)}: "
                f"{sanitize_for_log(payload)}"
            )

            # Parse JSON
            data = json.loads(payload)

            # Inject retain flag
            if hasattr(message, "retain"):
                data["_mqtt_retain"] = message.retain

            # Await the async message callback
            await self.message_callback(data)

        except json.JSONDecodeError as e:
            self.logger.warning(
                f"Failed to parse JSON message: {e}. "
                f"Payload: {sanitize_for_log(message.payload)}"
            )
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
