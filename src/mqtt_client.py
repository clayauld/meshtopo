"""
MQTT client for receiving Meshtastic position data.
"""

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import aiomqtt as mqtt

from utils import sanitize_for_log


class MqttClient:
    """
    Asynchronous MQTT client responsible for connecting to a broker,
    subscribing to configured topics, and routing incoming Meshtastic
    JSON messages to the application's processing logic.

    Handles automatic reconnection with exponential backoff.
    """

    def __init__(
        self,
        config: Any,
        message_callback: Callable[[Dict[str, Any], str], Awaitable[None]],
    ) -> None:
        """
        Initialize the MQTT client instance.

        Args:
            config: A Config object (see config/config.py) containing
                    broker address, credentials, and topic settings.
            message_callback: An asynchronous callable that receives the
                             parsed JSON payload as a dictionary.
        """
        self.config = config
        self.message_callback = message_callback
        self.client: Optional[mqtt.Client] = None
        self.logger = logging.getLogger(__name__)
        # To avoid duplicate processing of Protobuf vs JSON for same node/message
        self._processed_messages = set()

    async def _clean_processed_messages(self) -> None:
        """Periodically clean the processed messages cache to prevent memory leaks."""
        while True:
            await asyncio.sleep(60)  # Clean every 60 seconds
            self._processed_messages.clear()

    async def run(self) -> None:
        """
        Connect to the MQTT broker and process messages.
        This method will run indefinitely until cancelled.
        """
        reconnect_interval = 1
        max_reconnect_interval = 60

        # Start cleanup task
        cleanup_task = asyncio.create_task(self._clean_processed_messages())

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

                    # subscriptions must be refreshed on every successful (re)connection
                    topics = self.config.mqtt.topic
                    if isinstance(topics, str):
                        topics = [topics]
                    for t in topics:
                        await client.subscribe(t)
                        self.logger.info(f"Subscribed to topic: {t}")

                    # The client.messages generator yields messages as they arrive
                    async for message in client.messages:
                        await self._process_message(message)

            except mqtt.MqttError as e:
                self.logger.error(f"MQTT error: {e}")
            except asyncio.CancelledError:
                cleanup_task.cancel()
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
        Internal handler for incoming MQTT messages.
        Performs byte decoding, JSON parsing, and basic sanitization before
        invoking the application callback. For non-JSON messages, it decodes
        as protobuf ServiceEnvelope.

        Args:
            message: The raw message object from aiomqtt.
        """
        topic = str(message.topic)
        retain = getattr(message, "retain", False)

        # Check if JSON by topic convention
        is_json = "/json/" in topic

        # Deduplication based on topic pattern
        # If node ID is at the end, use it + channel for deduplication
        topic_parts = topic.split("/")
        if len(topic_parts) >= 5:
            # Topic format usually msh/<region>/2/<type>/<channel>/<node_id>
            # So msh/US/2/json/LongFast/!1234abcd
            channel = topic_parts[-2]
            node_id = topic_parts[-1]
            dedup_key = f"{channel}/{node_id}"

            # If we see JSON, we prefer it over protobuf and vice-versa
            # Actually, typically they arrive in the same second.
            if dedup_key in self._processed_messages:
                self.logger.debug(f"Skipping duplicate message for {dedup_key}")
                return

            self._processed_messages.add(dedup_key)

        try:
            if is_json:
                payload = message.payload.decode("utf-8")
                self.logger.debug(
                    f"Received JSON message on topic {sanitize_for_log(topic)}: "
                    f"{sanitize_for_log(payload)}"
                )
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"Failed to parse JSON message: {e}. "
                        f"Payload: {sanitize_for_log(payload)}"
                    )
                    return

                data["_mqtt_retain"] = retain
                await self.message_callback(data, topic)
            else:
                self.logger.debug(
                    f"Received non-JSON message on topic {sanitize_for_log(topic)}"
                )

                # Treat as protobuf, we pass the raw bytes dict to the app callback
                # We wrap it in a dict to reuse the existing pipeline interface.
                data = {
                    "_is_protobuf": True,
                    "_mqtt_retain": retain,
                    "payload_bytes": message.payload,
                }
                await self.message_callback(data, topic)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
