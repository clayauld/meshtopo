# Module `gateway_app`

Main gateway application that orchestrates MQTT and CalTopo communication.

## Classes

## `class GatewayApp`

Main application engine that orchestrates the Meshtastic-to-CalTopo gateway.

It manages the lifecycle of the MQTT client, handles state persistence for
node identification, and routes incoming position data to the CalTopo API.

### `def __init__(self, config_path: str = 'config/config.yaml')`

Initialize the gateway application instance.

Args:
    config_path: Filesystem path to the YAML configuration file.
                Defaults to 'config/config.yaml'.

### `def _convert_numeric_to_id(self, numeric_id: Union[int, str]) -> str`

Convert a numeric node ID to its standard Meshtastic string representation.

The standard format is an 8-character hex string prefixed with '!',
derived directly from the numeric ID.

Args:
    numeric_id: The numeric node ID (e.g., 24896776 or "24896776")

Returns:
    The formatted string ID (e.g., "!017bd508")

### `def _get_or_create_callsign(self, hardware_id: str) -> Optional[str]`

Resolve or create a callsign for a given hardware ID.

Args:
    hardware_id: The hardware ID to resolve.

Returns:
    The resolved callsign, or None if it cannot be resolved.

### `def _log_statistics(self) -> None`

Log current statistics.

### `def _persist_callsign_mapping(self, hardware_id: str, callsign: str) -> None`

Persist callsign mapping to cache and database.

### `def _persist_node_id_mapping(self, numeric_node_id: str, hardware_id: str) -> None`

Persist node ID mapping to cache and database.

### `def _process_message(self, data: Dict[str, Any]) -> None`

Core message dispatcher. Analyzes the 'type' field of incoming
Meshtastic JSON payloads and routes them to specific handlers.

Args:
    data: The parsed JSON payload from MQTT.

### `def _process_nodeinfo_message(self, data: Dict[str, Any], numeric_node_id: str) -> None`

Process a nodeinfo message.

Args:
    data: JSON data from Meshtastic
    numeric_node_id: Numeric node ID from the message

### `def _process_position_message(self, data: Dict[str, Any], numeric_node_id: str) -> None`

Specific handler for 'position' messages.
Extracts GPS coordinates, resolves device callsigns, and forwards
the update to the CalTopo Position Report API.

Args:
    data: The complete JSON message payload.
    numeric_node_id: The 'from' ID (numeric string) of the sender.

### `def _process_telemetry_message(self, data: Dict[str, Any], numeric_node_id: str) -> None`

Process a telemetry message.

Args:
    data: JSON data from Meshtastic
    numeric_node_id: Numeric node ID from the message

### `def _process_traceroute_message(self, data: Dict[str, Any], numeric_node_id: str) -> None`

Process a traceroute message.

Args:
    data: JSON data from Meshtastic
    numeric_node_id: Numeric node ID from the message

### `def _resolve_hardware_id(self, numeric_node_id: str) -> str`

Resolve hardware ID from numeric node ID using cache or calculation.
Does not persist new mappings.

### `def _stats_loop(self) -> None`

Log statistics periodically.

### `def close(self) -> None`

Close all resources.

### `def initialize(self) -> bool`

Perform a comprehensive startup sequence for all application components.
This includes loading configuration, initializing the persistent database,
setting up HTTP clients, and preparing the MQTT subscriber.

Returns:
    bool: True if all components initialized successfully; False if a
          critical failure occurred.

### `def start(self) -> None`

Execute the primary application loop.
Initializes components and then enters a long-running state until
a stop signal or fatal error occurs.

### `def stop(self) -> None`

Stop the gateway service gracefully.
