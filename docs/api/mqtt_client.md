# Module `mqtt_client`

MQTT client for receiving Meshtastic position data.

## Classes

## `class MqttClient`

MQTT client for connecting to broker and receiving Meshtastic data.

### `def __init__(self, config: Any, message_callback: Callable[[Dict[str, Any]], Awaitable[NoneType]]) -> None`

Initialize MQTT client.

Args:
    config: Configuration object containing MQTT settings
    message_callback: Async function to call when a message is received

### `def run(self) -> None`

Connect to the MQTT broker and process messages.
This method will run indefinitely until cancelled.
