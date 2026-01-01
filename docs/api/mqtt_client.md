<!-- markdownlint-disable-file MD046 -->

# Module `mqtt_client`

AsyncIO MQTT Client Wrapper

This module provides a robust wrapper around `aiomqtt` (which wraps `paho-mqtt`)
to handle connection management, subscription, and message dispatch.

## Features

* **Automatic Reconnection:** Implements an infinite loop with exponential backoff
    to handle broker disconnections and network instability.
* **Async Stream:** Consumes messages from `aiomqtt.Client.messages` async generator.
* **Security:** Handles authentication via username/password (from `SecretStr`).

## Usage

Instantiate `MqttClient` with a configuration object and a callback function.
Then, `await client.run()` to start the connection loop. This method blocks
until cancelled.

## Classes

## `class MqttClient`

Manages the MQTT connection life-cycle.

### `def __init__(self, config: Any, message_callback: Callable[[Dict[str, Any]], Awaitable[NoneType]]) -> None`

Initialize MQTT client.

Args:
    config: Configuration object containing MQTT settings (broker, port, etc.)
    message_callback: Async function to call when a valid JSON message is
                      received.

### `def run(self) -> None`

Main connection loop.

Connects to the broker, subscribes to topics, and processes messages.
If the connection drops, it catches the `MqttError`, waits, and retries.

The backoff strategy starts at 1s and doubles up to 60s.
