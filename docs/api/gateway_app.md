<!-- markdownlint-disable-file MD046 -->

# Module `gateway_app`

Main Gateway Application Logic

This module contains the `GatewayApp` class, which is the heart of the Meshtopo service.
It orchestrates data between MQTT and CalTopo.

## Architecture

The application is built on an asynchronous event loop (`asyncio`) to ensure non-blocking
operation, which is critical for handling network I/O from both MQTT and HTTP
simultaneously.

### Core Components

1. **MqttClient (`aiomqtt`):** Handles the persistent connection to the MQTT broker.
    It runs in a dedicated task and pushes incoming messages to the `_process_message`
    callback.
2. **CalTopoReporter (`httpx`):** Manages the connection to CalTopo. It uses a shared
    `httpx.AsyncClient` for connection pooling and implements exponential backoff for
    reliability.
3. **PersistentDict:** Provides durable state storage for mapping Node IDs to User
    Metadata.
    This replaces the older `sqlitedict` implementation to avoid pickle security risks.

### Data Flow

1. **Ingest:** `MqttClient` receives a JSON payload from a subscribed topic.
2. **Route:** `_process_message` determines the message type (position, nodeinfo,
    etc.).
3. **Process:**
    * **NodeInfo:** Updates the `node_id_mapping` and `callsign_mapping` persistent
        stores.
        This allows the system to "learn" new nodes and their callsigns.
    * **Position:** Looks up the `hardware_id` and `callsign` using the persistent
        state.
        If found, it forwards the coordinates to `CalTopoReporter`.
4. **Report:** `CalTopoReporter` sends the data to the configured CalTopo map(s).

### State Management

The application maintains two critical mappings:

* `node_id_mapping`: Numeric Node ID (from Meshtastic packet) -> Hardware ID (e.g.,
    "!abcdef12")
* `callsign_mapping`: Hardware ID -> Callsign (Display Name)

These are backed by a SQLite database (`meshtopo_state.sqlite`) using JSON serialization
to ensure data survives application restarts.

## Classes

## `class GatewayApp`

Main application orchestrator.

Lifecycle:

1. `__init__`: Sets up basic state containers.
2. `initialize`: Asynchronous setup. Loads config, opens DB, connects HTTP client.
    Must be called before `start`.
3. `start`: Main entry point. Connects MQTT and blocks on `stop_event`.
4. `stop`: Graceful shutdown. Closes connections and resources.

### `def __init__(self, config_path: str = 'config/config.yaml')`

Initialize the gateway application instance.

Args:
    config_path: Path to the configuration file

### `def close(self) -> None`

Close database resources specifically.

### `def initialize(self) -> bool`

Perform asynchronous initialization of all components.

This method handles:

1. Loading configuration.
2. Setting up logging.
3. Opening/Creating the SQLite state database.
4. Initializing the shared HTTP client.
5. Initializing the CalTopo reporter and MQTT client.

Returns:
    bool: True if initialization was successful, False otherwise.

### `def start(self) -> None`

Start the gateway service.

This is the main blocking call. It:

1. Initializes the app.
2. Starts the MQTT client task.
3. Starts the statistics logging task.
4. Waits for `stop_event`.

### `def stop(self) -> None`

Stop the gateway service gracefully.
Closes all network connections and database handles.
