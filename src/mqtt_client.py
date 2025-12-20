"""
MQTT client for receiving Meshtastic position data.
"""

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import aiomqtt as mqtt


class MqttClient:
    """
    MQTT client for connecting to broker and receiving Meshtastic data.
    """

    def __init__(
        self,
        config: Any,
        message_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
        Initialize MQTT client.

        Args:
            config: Configuration object containing MQTT settings
            message_callback: Async function to call when a message is received
        """
        self.config = config
        self.message_callback = message_callback
        self.client: Optional[mqtt.Client] = None
        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        """
        Connect to the MQTT broker and process messages.
        This method will run indefinitely until cancelled.
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
                    password=self.config.mqtt.password,
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
        Process a received MQTT message.

        Args:
            message: The received message object
        """
        try:
            payload = message.payload.decode("utf-8")
            # Use lazy logging to avoid string formatting overhead if debug is disabled
            self.logger.debug("Received message on topic %s: %s", message.topic, payload)

            # Parse JSON
            data = json.loads(payload)

            # Inject retain flag
            if hasattr(message, "retain"):
                data["_mqtt_retain"] = message.retain

            # Await the async message callback
            await self.message_callback(data)

        except json.JSONDecodeError as e:
            self.logger.warning(
                f"Failed to parse JSON message: {e}. Payload: {message.payload}"
            )
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
