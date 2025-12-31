"""
Main Gateway Application Logic

This module contains the `GatewayApp` class, which is the heart of the Meshtopo service.
It orchestrates the flow of data between the MQTT broker (Meshtastic source) and the
CalTopo API (reporter destination).

## Architecture

The application is built on an asynchronous event loop (`asyncio`) to ensure non-blocking
operation, which is critical for handling network I/O from both MQTT and HTTP simultaneously.

### Core Components
1.  **MqttClient (`aiomqtt`):** Handles the persistent connection to the MQTT broker.
    It runs in a dedicated task and pushes incoming messages to the `_process_message` callback.
2.  **CalTopoReporter (`httpx`):** Manages the connection to CalTopo. It uses a shared
    `httpx.AsyncClient` for connection pooling and implements exponential backoff for reliability.
3.  **PersistentDict:** Provides durable state storage for mapping Node IDs to User Metadata.
    This replaces the older `sqlitedict` implementation to avoid pickle security risks.

### Data Flow
1.  **Ingest:** `MqttClient` receives a JSON payload from a subscribed topic.
2.  **Route:** `_process_message` determines the message type (position, nodeinfo, etc.).
3.  **Process:**
    *   **NodeInfo:** Updates the `node_id_mapping` and `callsign_mapping` persistent stores.
        This allows the system to "learn" new nodes and their callsigns.
    *   **Position:** Looks up the `hardware_id` and `callsign` using the persistent state.
        If found, it forwards the coordinates to `CalTopoReporter`.
4.  **Report:** `CalTopoReporter` sends the data to the configured CalTopo map(s).

### State Management
The application maintains two critical mappings:
*   `node_id_mapping`: Numeric Node ID (from Meshtastic packet) -> Hardware ID (e.g., "!abcdef12")
*   `callsign_mapping`: Hardware ID -> Callsign (Display Name)

These are backed by a SQLite database (`meshtopo_state.sqlite`) using JSON serialization
to ensure data survives application restarts.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict, Optional, Union

import httpx

from caltopo_reporter import CalTopoReporter
from config.config import Config
from mqtt_client import MqttClient
from persistent_dict import PersistentDict
from utils import sanitize_for_log


class GatewayApp:
    """
    Main application orchestrator.

    Lifecycle:
    1.  `__init__`: Sets up basic state containers.
    2.  `initialize`: Asynchronous setup. Loads config, opens DB, connects HTTP client.
        Must be called before `start`.
    3.  `start`: Main entry point. Connects MQTT and blocks on `stop_event`.
    4.  `stop`: Graceful shutdown. Closes connections and resources.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the gateway application instance.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.mqtt_client: Optional[MqttClient] = None
        self.caltopo_reporter: Optional[CalTopoReporter] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.stop_event: Optional[asyncio.Event] = None
        self.logger = logging.getLogger(__name__)

        # Statistics tracking
        self.stats: Dict[str, Union[int, float]] = {
            "messages_received": 0,
            "messages_processed": 0,
            "position_updates_sent": 0,
            "errors": 0,
            "start_time": 0.0,
        }

        # Persistent state (initialized in self.initialize)
        # We use Any here because the PersistentDict type is generic but simple
        self.node_id_mapping: Any = None
        self.callsign_mapping: Any = None

        # In-memory caches for performance to avoid disk I/O on every packet
        self._node_id_cache: Dict[str, str] = {}
        self._callsign_cache: Dict[str, str] = {}

        self.configured_devices: set = (
            set()
        )  # Track which devices are explicitly defined in config

    async def initialize(self) -> bool:
        """
        Perform asynchronous initialization of all components.

        This method handles:
        1.  Loading configuration.
        2.  Setting up logging.
        3.  Opening/Creating the SQLite state database.
        4.  Initializing the shared HTTP client.
        5.  Initializing the CalTopo reporter and MQTT client.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Load configuration
            self.logger.info("Loading configuration...")
            self.config = Config.from_file(self.config_path)

            # Setup logging
            self.config.setup_logging()
            self.logger.info("Configuration loaded successfully")

            # Initialize persistent state
            db_path = self.config.storage.db_path
            self.logger.info(f"Using database file: {db_path}")

            # Ensure database directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir:
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    self.logger.error(
                        f"Failed to create database directory {db_dir}: {e}"
                    )
                    # We continue, letting PersistentDict fail if it must

            try:
                # We use PersistentDict (custom wrapper around sqlite3) instead of sqlitedict
                # to ensure we use JSON serialization. Pickle is unsafe for untrusted data.
                self.node_id_mapping = PersistentDict(
                    db_path,
                    tablename="node_id_mapping",
                    autocommit=True,
                )
                # Trigger a read to ensure the file format is valid
                _ = len(self.node_id_mapping)

                self.callsign_mapping = PersistentDict(
                    db_path,
                    tablename="callsign_mapping",
                    autocommit=True,
                )
                _ = len(self.callsign_mapping)

                # Load into memory cache for faster lookups
                self.logger.info("Loading state into memory cache...")
                self._node_id_cache = dict(self.node_id_mapping)
                self._callsign_cache = dict(self.callsign_mapping)

            except Exception as e:
                self.logger.warning(
                    f"Failed to load state database (likely due to format change): "
                    f"{e}. Resetting state file."
                )
                self.close() # Close any open handles

                # Delete the incompatible file
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                    except OSError as remove_error:
                        self.logger.error(
                            f"Failed to remove incompatible database file: "
                            f"{remove_error}"
                        )

                # Re-initialize with new format
                self.node_id_mapping = PersistentDict(
                    db_path,
                    tablename="node_id_mapping",
                    autocommit=True,
                )
                self.callsign_mapping = PersistentDict(
                    db_path,
                    tablename="callsign_mapping",
                    autocommit=True,
                )

                # Reset cache
                self._node_id_cache = dict(self.node_id_mapping)
                self._callsign_cache = dict(self.callsign_mapping)

            # Check if we should use internal MQTT broker
            if self.config.mqtt.use_internal_broker:
                self.logger.info("Using internal MQTT broker")
                # Update broker hostname to use internal service name
                self.config.mqtt.broker = "mosquitto"

            # Initialize Shared HTTP Client
            # Connection pooling is handled here.
            self.http_client = httpx.AsyncClient(timeout=10)

            # Initialize CalTopo reporter with shared client
            self.logger.info("Initializing CalTopo reporter...")
            self.caltopo_reporter = CalTopoReporter(
                self.config, client=self.http_client
            )
            await self.caltopo_reporter.start()

            # Test CalTopo connectivity early
            if not await self.caltopo_reporter.test_connection():
                self.logger.warning(
                    "CalTopo API connectivity test failed, but continuing..."
                )

            # Initialize MQTT client
            self.logger.info("Initializing MQTT client...")
            self.mqtt_client = MqttClient(self.config, self._process_message)

            # Build set of configured devices for tracking
            self.configured_devices = set(self.config.nodes.keys())
            self.logger.info(f"Configured devices: {self.configured_devices}")

            # Create stop event for the main loop
            self.stop_event = asyncio.Event()

            self.logger.info("Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    async def start(self) -> None:
        """
        Start the gateway service.

        This is the main blocking call. It:
        1. Initializes the app.
        2. Starts the MQTT client task.
        3. Starts the statistics logging task.
        4. Waits for `stop_event`.
        """
        try:
            if not await self.initialize():
                self.logger.error("Failed to initialize application. Exiting.")
                sys.exit(1)

            self.logger.info("Starting Meshtopo gateway service...")
            self.stats["start_time"] = time.time()

            if self.mqtt_client is None:
                self.logger.error("MQTT client not initialized. Exiting.")
                sys.exit(1)

            # Create background tasks
            # mqtt_client.run() is an infinite loop that handles reconnection
            mqtt_task = asyncio.create_task(self.mqtt_client.run())
            stats_task = asyncio.create_task(self._stats_loop())

            self.logger.info("Gateway service started successfully")

            # Wait for stop event (triggered by signal or error)
            if not self.stop_event:
                raise RuntimeError("GatewayApp not initialized: stop_event is None")
            await self.stop_event.wait()

            # Graceful shutdown sequence
            mqtt_task.cancel()
            stats_task.cancel()

            # Wait for tasks to finish (suppress cancellation errors)
            await asyncio.gather(mqtt_task, stats_task, return_exceptions=True)

        except asyncio.CancelledError:
            self.logger.info("Service cancelled")
        except Exception as e:
            self.logger.error(f"Fatal error in service: {e}")
        finally:
            await self.stop()

    async def _stats_loop(self) -> None:
        """Log statistics every 60 seconds."""
        while self.stop_event and not self.stop_event.is_set():
            await asyncio.sleep(60)
            self._log_statistics()

    async def stop(self) -> None:
        """
        Stop the gateway service gracefully.
        Closes all network connections and database handles.
        """
        self.logger.info("Stopping gateway service...")
        if self.stop_event:
            self.stop_event.set()

        # Close CalTopo reporter
        if self.caltopo_reporter:
            await self.caltopo_reporter.close()

        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()

        # Close database connections
        self.close()

        # Log final statistics
        self._log_statistics()
        self.logger.info("Gateway service stopped")

    def close(self) -> None:
        """Close database resources specifically."""
        self.logger.info("Closing database connections...")
        if self.node_id_mapping and hasattr(self.node_id_mapping, "close"):
            self.node_id_mapping.close()
        if self.callsign_mapping and hasattr(self.callsign_mapping, "close"):
            self.callsign_mapping.close()

    def _resolve_hardware_id(self, numeric_node_id: str) -> str:
        """
        Resolve hardware ID from numeric node ID using cache or calculation.

        Meshtastic nodes have a numeric ID (e.g., 12345) and a hardware ID (e.g., !abcd).
        We prefer to look up the hardware ID from previous NodeInfo packets, but if unknown,
        we can deterministically convert the numeric ID to the hardware ID format.
        """
        if numeric_node_id in self._node_id_cache:
            return self._node_id_cache[numeric_node_id]

        return self._convert_numeric_to_id(numeric_node_id)

    def _persist_node_id_mapping(self, numeric_node_id: str, hardware_id: str) -> None:
        """Persist node ID mapping to cache and database."""
        if self._node_id_cache.get(numeric_node_id) == hardware_id:
            return

        self._node_id_cache[numeric_node_id] = hardware_id
        if self.node_id_mapping is not None:
            self.node_id_mapping[numeric_node_id] = hardware_id

    def _persist_callsign_mapping(self, hardware_id: str, callsign: str) -> None:
        """Persist callsign mapping to cache and database."""
        if self._callsign_cache.get(hardware_id) == callsign:
            return

        self._callsign_cache[hardware_id] = callsign
        if self.callsign_mapping is not None:
            self.callsign_mapping[hardware_id] = callsign

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """
        Process a message received from MQTT.

        Dispatches to specific handlers based on the 'type' field in the JSON payload.
        """
        self.stats["messages_received"] += 1

        try:
            # Extract numeric node ID
            numeric_node_id = data.get("from")
            if not numeric_node_id:
                self.logger.warning("Received message without from field")
                return

            # Check message type and process accordingly
            message_type = data.get("type")
            if message_type == "position":
                await self._process_position_message(data, numeric_node_id)
            elif message_type == "nodeinfo":
                self._process_nodeinfo_message(data, numeric_node_id)
            elif message_type == "telemetry":
                self._process_telemetry_message(data, numeric_node_id)
            elif message_type == "traceroute":
                self._process_traceroute_message(data, numeric_node_id)
            elif message_type == "":
                self.logger.debug(
                    f"Received message with empty type from "
                    f"{sanitize_for_log(numeric_node_id)}, skipping"
                )
                return
            else:
                self.logger.debug(
                    f"Received unsupported message type from "
                    f"{sanitize_for_log(numeric_node_id)}: "
                    f"{sanitize_for_log(message_type)}"
                )
                return

            self.stats["messages_processed"] += 1

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1

    def _get_or_create_callsign(self, hardware_id: str) -> Optional[str]:
        """
        Resolve or create a callsign for a given hardware ID.

        Logic:
        1.  **Configured Device:** If the ID is in `config.yaml`, use the configured name.
        2.  **Learned Device:** If we have seen a NodeInfo packet, use the cached callsign.
        3.  **Unknown Device:** If `allow_unknown_devices` is True, use the hardware ID.
            Otherwise, return None to block the update.
        """
        if self.config is None:
            self.logger.error("Configuration not loaded")
            return None

        # Check configured devices FIRST - Configuration always overrides persistence
        configured_device_id = self.config.get_node_device_id(hardware_id)
        if configured_device_id:
            self.logger.debug(
                f"Using configured device_id as callsign: "
                f"{sanitize_for_log(hardware_id)} -> "
                f"{sanitize_for_log(configured_device_id)}"
            )
            return configured_device_id

        # Check cache SECOND (for learned/discovered nodes)
        callsign = self._callsign_cache.get(hardware_id)
        if callsign:
            return callsign

        # Handle unknown/unconfigured devices
        is_unknown_device = hardware_id not in self.configured_devices

        if is_unknown_device:
            if self.config.devices.allow_unknown_devices:
                # Allow unknown device but use hardware_id as callsign
                self.logger.info(
                    f"Allowing unknown device {sanitize_for_log(hardware_id)} "
                    f"(allow_unknown_devices=True). Using hardware_id as callsign."
                )
                return hardware_id
            else:
                self.logger.warning(
                    f"Unknown device {sanitize_for_log(hardware_id)} "
                    f"position update blocked (allow_unknown_devices=False). "
                    f"Device is tracked but no position sent."
                )
                return None

        # Known device but no callsign mapping
        self.logger.warning(
            f"No callsign mapping found for known hardware ID "
            f"{sanitize_for_log(hardware_id)}. Position update will be "
            f"skipped until nodeinfo message is received."
        )
        return None

    def _convert_numeric_to_id(self, numeric_id: Union[int, str]) -> str:
        """
        Convert a numeric node ID to its standard Meshtastic string representation.

        The standard format is an 8-character hex string prefixed with '!',
        derived directly from the numeric ID.

        Args:
            numeric_id: The numeric node ID (e.g., 24896776 or "24896776")

        Returns:
            The formatted string ID (e.g., "!017bd508")
        """
        try:
            # Ensure we have an integer
            val = int(numeric_id)
            # Format as 8-character lowercase hex with ! prefix
            return f"!{val:08x}"
        except (ValueError, TypeError):
            self.logger.warning(
                f"Could not convert numeric ID to string: "
                f"{sanitize_for_log(numeric_id)}"
            )
            return f"!{str(numeric_id)}"

    async def _process_position_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """
        Process a position message.

        Extracts lat/lon, resolves the user, and sends to CalTopo.
        """
        if self.node_id_mapping is None or self.callsign_mapping is None:
            self.logger.error("State databases not initialized")
            self.stats["errors"] += 1
            return

        # Check for retained message
        if data.get("_mqtt_retain"):
            self.logger.info(
                f"Skipping retained position message from "
                f"{sanitize_for_log(numeric_node_id)}"
            )
            return

        # Extract payload
        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received position message from "
                f"{sanitize_for_log(numeric_node_id)} without payload"
            )
            return

        # Extract coordinates
        latitude_i = payload.get("latitude_i")
        longitude_i = payload.get("longitude_i")

        if latitude_i is None or longitude_i is None:
            self.logger.warning(
                f"Received position message from "
                f"{sanitize_for_log(numeric_node_id)} without coordinates"
            )
            return

        # Convert to decimal degrees
        latitude = latitude_i / 1e7
        longitude = longitude_i / 1e7

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                f"Processing position from "
                f"{sanitize_for_log(numeric_node_id)}: "
                f"{latitude}, {longitude}"
            )

        # Send to CalTopo
        if self.caltopo_reporter is None:
            self.logger.error("CalTopo reporter not initialized")
            self.stats["errors"] += 1
            return

        # Get the hardware ID for this numeric node ID
        hardware_id = self._resolve_hardware_id(str(numeric_node_id))
        is_new_mapping = str(numeric_node_id) not in self._node_id_cache

        # Get callsign for this hardware ID
        callsign = self._get_or_create_callsign(hardware_id)
        if not callsign:
            if self.config is None:
                self.stats["errors"] += 1
            return

        # Device is allowed (we have a callsign). Now we can persist the node ID mapping
        if is_new_mapping:
            self._persist_node_id_mapping(str(numeric_node_id), hardware_id)

        # Get GROUP for this device (if using group-based API)
        group = None
        if self.config is not None and self.config.caltopo.has_group:
            group = self.config.get_node_group(hardware_id) or self.config.caltopo.group

        success = await self.caltopo_reporter.send_position_update(
            callsign, latitude, longitude, group
        )

        if success:
            self.stats["position_updates_sent"] += 1
        else:
            self.stats["errors"] += 1

    def _process_nodeinfo_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """
        Process a nodeinfo message to learn node Metadata.

        Updates the persistent `node_id_mapping` and `callsign_mapping`.
        This allows the system to auto-discover nodes on the mesh.
        """
        if self.node_id_mapping is None or self.callsign_mapping is None:
            self.logger.error("State databases not initialized")
            return

        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received nodeinfo message from {numeric_node_id} without payload"
            )
            return

        # Extract node information
        node_id_from_payload = payload.get("id")
        longname = payload.get("longname")
        shortname = payload.get("shortname")
        hardware = payload.get("hardware")
        role = payload.get("role")

        # Build mapping from numeric node ID to hardware ID
        if node_id_from_payload:
            self._persist_node_id_mapping(str(numeric_node_id), node_id_from_payload)
            self.logger.debug(
                f"Mapped numeric node ID {sanitize_for_log(numeric_node_id)} "
                f"to hardware ID {sanitize_for_log(node_id_from_payload)}"
            )

            # Extract and store callsign - prioritize configured device_id over
            # Meshtastic longname
            if self.config is None:
                self.logger.error("Configuration not loaded")
                return
            configured_device_id = self.config.get_node_device_id(node_id_from_payload)
            if configured_device_id:
                # Use configured device_id as callsign
                self._persist_callsign_mapping(
                    node_id_from_payload, configured_device_id
                )
            elif longname:
                # Fallback to Meshtastic longname if no configured device_id
                self._persist_callsign_mapping(node_id_from_payload, longname)
            elif shortname:
                # Final fallback to shortname if longname not available
                self._persist_callsign_mapping(node_id_from_payload, shortname)

        self.logger.info(
            f"Node info from {sanitize_for_log(numeric_node_id)}: "
            f"ID={sanitize_for_log(node_id_from_payload)}, "
            f"Name={sanitize_for_log(longname)} "
            f"({sanitize_for_log(shortname)}), "
            f"Hardware={sanitize_for_log(hardware)}, "
            f"Role={sanitize_for_log(role)}"
        )

    def _process_telemetry_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """
        Process a telemetry message. Logs stats but does not currently action them.
        """
        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received telemetry message from {numeric_node_id} without payload"
            )
            return

        # Extract telemetry data
        battery_level = payload.get("battery_level")
        voltage = payload.get("voltage")
        uptime_seconds = payload.get("uptime_seconds")
        air_util_tx = payload.get("air_util_tx")
        channel_utilization = payload.get("channel_utilization")

        self.logger.info(
            f"Telemetry from {sanitize_for_log(numeric_node_id)}: "
            f"Battery={sanitize_for_log(battery_level)}%, "
            f"Voltage={sanitize_for_log(voltage)}V, "
            f"Uptime={sanitize_for_log(uptime_seconds)}s, "
            f"Air util TX={sanitize_for_log(air_util_tx)}, "
            f"Channel util={sanitize_for_log(channel_utilization)}%"
        )

    def _process_traceroute_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """Process a traceroute message. Logs only."""
        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received traceroute message from {numeric_node_id} without payload"
            )
            return

        route = payload.get("route", [])

        self.logger.info(
            f"Traceroute from {sanitize_for_log(numeric_node_id)}: "
            f"Route={sanitize_for_log(route)}"
        )

    def _log_statistics(self) -> None:
        """Log current statistics for health monitoring."""
        if not self.stats["start_time"]:
            return

        uptime = time.time() - self.stats["start_time"]
        self.logger.info(
            f"Statistics - Uptime: {uptime: .0f}s, "
            f"Messages received: {self.stats['messages_received']}, "
            f"Messages processed: {self.stats['messages_processed']}, "
            f"Position updates sent: {self.stats['position_updates_sent']}, "
            f"Errors: {self.stats['errors']}"
        )
