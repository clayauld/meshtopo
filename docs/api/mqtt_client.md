# Module `mqtt_client`

MQTT client for receiving Meshtastic position data.

## Classes

## `class MqttClient`

Asynchronous MQTT client responsible for connecting to a broker,
subscribing to configured topics, and routing incoming Meshtastic
JSON messages to the application's processing logic.

Handles automatic reconnection with exponential backoff.

### `def __init__(self, config: Any, message_callback: Callable[[Dict[str, Any]], Awaitable[NoneType]]) -> None`

Initialize the MQTT client instance.

Args:
    config: A Config object (see config/config.py) containing
            broker address, credentials, and topic settings.
    message_callback: An asynchronous callable that receives the
                     parsed JSON payload as a dictionary.

### `def _process_message(self, message: Any) -> None`

Internal handler for incoming MQTT messages.
Performs byte decoding, JSON parsing, and basic sanitization before
invoking the application callback.

Args:
    message: The raw message object from aiomqtt.

### `def run(self) -> None`

Connect to the MQTT broker and process messages.
This method will run indefinitely until cancelled.
