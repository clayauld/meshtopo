"""
Main gateway application that orchestrates MQTT and CalTopo communication.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional, Union

from sqlitedict import SqliteDict

from caltopo_reporter import CalTopoReporter
from config.config import Config
from mqtt_client import MqttClient
from utils import sanitize_for_log


class GatewayApp:
    """
    Main application class that orchestrates the gateway service.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the gateway application.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.mqtt_client: Optional[MqttClient] = None
        self.caltopo_reporter: Optional[CalTopoReporter] = None
        self.stop_event: Optional[asyncio.Event] = None
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats: Dict[str, Union[int, float]] = {
            "messages_received": 0,
            "messages_processed": 0,
            "position_updates_sent": 0,
            "errors": 0,
            "start_time": 0.0,
        }

        # Persistent state using sqlitedict
        self.node_id_mapping: Optional[Dict[str, str]] = None
        self.callsign_mapping: Optional[Dict[str, str]] = None
        self.configured_devices: set = (
            set()
        )  # Track which devices are in the nodes config

    async def initialize(self) -> bool:
        """
        Initialize the application components.

        Returns:
            bool: True if initialization successful, False otherwise
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
                    # We continue, letting SqliteDict fail if it must, or maybe it works

            self.node_id_mapping = SqliteDict(
                db_path,
                tablename="node_id_mapping_v2",
                autocommit=True,
                encode=json.dumps,
                decode=json.loads,
            )
            self.callsign_mapping = SqliteDict(
                db_path,
                tablename="callsign_mapping_v2",
                autocommit=True,
                encode=json.dumps,
                decode=json.loads,
            )

            # Check if we should use internal MQTT broker
            if self.config.mqtt.use_internal_broker:
                self.logger.info("Using internal MQTT broker")
                # Update broker hostname to use internal service name
                self.config.mqtt.broker = "mosquitto"

            # Initialize CalTopo reporter
            self.logger.info("Initializing CalTopo reporter...")
            self.caltopo_reporter = CalTopoReporter(self.config)
            await self.caltopo_reporter.start()

            # Test CalTopo connectivity
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

            # Create stop event in the running loop
            self.stop_event = asyncio.Event()

            self.logger.info("Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    async def start(self) -> None:
        """
        Start the gateway service.
        """
        try:
            if not await self.initialize():
                self.logger.error("Failed to initialize application. Exiting.")
                sys.exit(1)

            # Setup signal handlers for graceful shutdown (managed by main loop really,
            # but we can hook into asyncio loop too if needed, or just let the caller
            # handle it.
            # Gateway.py handles signals by calling stop().
            # Note: signal.signal only works in main thread.
            # We'll rely on the caller to cancel the tasks or set the stop event.
            # But let's keep the logging here if logical.

            self.logger.info("Starting Meshtopo gateway service...")
            self.stats["start_time"] = time.time()

            # Connect to MQTT broker
            if self.mqtt_client is None:
                self.logger.error("MQTT client not initialized. Exiting.")
                sys.exit(1)

            # Create tasks
            mqtt_task = asyncio.create_task(self.mqtt_client.run())
            stats_task = asyncio.create_task(self._stats_loop())

            self.logger.info("Gateway service started successfully")

            # Wait for stop event
            if not self.stop_event:
                raise RuntimeError("GatewayApp not initialized: stop_event is None")
            await self.stop_event.wait()

            # Cancel tasks
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
        """Log statistics periodically."""
        while self.stop_event and not self.stop_event.is_set():
            await asyncio.sleep(60)
            self._log_statistics()

    async def stop(self) -> None:
        """
        Stop the gateway service gracefully.
        """
        self.logger.info("Stopping gateway service...")
        if self.stop_event:
            self.stop_event.set()

        # Close CalTopo reporter
        if self.caltopo_reporter:
            await self.caltopo_reporter.close()

        # Close database connections
        self.close()

        # Log final statistics
        self._log_statistics()
        self.logger.info("Gateway service stopped")

    def close(self) -> None:
        """Close all resources."""
        self.logger.info("Closing database connections...")
        if self.node_id_mapping and hasattr(self.node_id_mapping, "close"):
            self.node_id_mapping.close()
        if self.callsign_mapping and hasattr(self.callsign_mapping, "close"):
            self.callsign_mapping.close()

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """
        Process a message received from MQTT.

        Args:
            data: JSON data from Meshtastic
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
                    f"Received message with empty type from {numeric_node_id}, skipping"
                )
                return
            else:
                self.logger.debug(
                    f"Received unsupported message type from {numeric_node_id}: "
                    f"{message_type}"
                )
                return

            self.stats["messages_processed"] += 1

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1

    def _get_or_create_callsign(self, hardware_id: str) -> Optional[str]:
        """
        Resolve or create a callsign for a given hardware ID.

        Args:
            hardware_id: The hardware ID to resolve.

        Returns:
            The resolved callsign, or None if it cannot be resolved.
        """
        if self.config is None:
            self.logger.error("Configuration not loaded")
            return None

        # Check configured devices FIRST - Configuration always overrides persistence
        configured_device_id = self.config.get_node_device_id(hardware_id)
        if configured_device_id:
            # We do NOT write this to the database anymore.
            # Configuration is the source of truth.
            # This prevents stale config from persisting if removed from
            # config.yaml.
            self.logger.debug(
                f"Using configured device_id as callsign: "
                f"{hardware_id} -> {configured_device_id}"
            )
            return configured_device_id

        # Check mapping database SECOND (for learned/discovered nodes)
        if self.callsign_mapping:
            callsign = self.callsign_mapping.get(hardware_id)
            if callsign:
                return callsign
        else:
            self.logger.warning("Callsign mapping database not initialized")

        # Handle unknown/unconfigured devices
        is_unknown_device = hardware_id not in self.configured_devices

        if is_unknown_device:
            if self.config.devices.allow_unknown_devices:
                # Allow unknown device but use hardware_id as callsign
                callsign = hardware_id
                if self.callsign_mapping is not None:
                    self.callsign_mapping[hardware_id] = callsign
                self.logger.info(
                    f"Allowing unknown device {hardware_id} "
                    f"(allow_unknown_devices=True). Using hardware_id as callsign."
                )
                return callsign
            else:
                self.logger.warning(
                    f"Unknown device {hardware_id} position update blocked "
                    f"(allow_unknown_devices=False). Device is tracked but no "
                    f"position sent."
                )
                return None

        # Known device but no callsign mapping
        self.logger.warning(
            f"No callsign mapping found for known hardware ID "
            f"{hardware_id}. Position update will be skipped until "
            f"nodeinfo message is received."
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
            # Fallback for invalid inputs, though unlikely with correct upstream parsing
            self.logger.warning(f"Could not convert numeric ID to string: {numeric_id}")
            return f"!{str(numeric_id)}"

    async def _process_position_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """
        Process a position message.

        Args:
            data: JSON data from Meshtastic
            numeric_node_id: Numeric node ID from the message
        """
        if self.node_id_mapping is None or self.callsign_mapping is None:
            self.logger.error("State databases not initialized")
            self.stats["errors"] += 1
            return

        # Check for retained message
        if data.get("_mqtt_retain"):
            self.logger.info(
                f"Skipping retained position message from {numeric_node_id}"
            )
            return

        # Extract payload
        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received position message from {numeric_node_id} without payload"
            )
            return

        # Extract coordinates
        latitude_i = payload.get("latitude_i")
        longitude_i = payload.get("longitude_i")

        if latitude_i is None or longitude_i is None:
            self.logger.warning(
                f"Received position message from {numeric_node_id} without coordinates"
            )
            return

        # Convert to decimal degrees
        latitude = latitude_i / 1e7
        longitude = longitude_i / 1e7

        self.logger.debug(
            f"Processing position from {numeric_node_id}: {latitude}, {longitude}"
        )

        # Send to CalTopo
        if self.caltopo_reporter is None:
            self.logger.error("CalTopo reporter not initialized")
            self.stats["errors"] += 1
            return

        # Get the hardware ID for this numeric node ID
        hardware_id = self.node_id_mapping.get(str(numeric_node_id))

        # If we haven't seen this node before, calculate its ID deterministically
        if not hardware_id:
            hardware_id = self._convert_numeric_to_id(numeric_node_id)

            # Save this calculated mapping to the database
            self.node_id_mapping[str(numeric_node_id)] = hardware_id
            self.logger.debug(
                f"Calculated ID for new node: {numeric_node_id} -> {hardware_id}"
            )

        # Get callsign for this hardware ID
        callsign = self._get_or_create_callsign(hardware_id)
        if not callsign:
            if self.config is None:
                self.stats["errors"] += 1
            return

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
        Process a nodeinfo message.

        Args:
            data: JSON data from Meshtastic
            numeric_node_id: Numeric node ID from the message
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
            self.node_id_mapping[str(numeric_node_id)] = node_id_from_payload
            self.logger.debug(
                f"Mapped numeric node ID {numeric_node_id} to hardware ID "
                f"{node_id_from_payload}"
            )

            # Extract and store callsign - prioritize configured device_id over
            # Meshtastic longname
            if self.config is None:
                self.logger.error("Configuration not loaded")
                return
            configured_device_id = self.config.get_node_device_id(node_id_from_payload)
            if configured_device_id:
                # Use configured device_id as callsign
                self.callsign_mapping[node_id_from_payload] = configured_device_id
                self.logger.debug(
                    f"Mapped hardware ID {node_id_from_payload} to configured "
                    f"callsign {configured_device_id}"
                )
            elif longname:
                # Fallback to Meshtastic longname if no configured device_id
                self.callsign_mapping[node_id_from_payload] = longname
                self.logger.debug(
                    f"Mapped hardware ID {node_id_from_payload} to callsign "
                    f"{longname} (from longname)"
                )
            elif shortname:
                # Final fallback to shortname if longname not available
                self.callsign_mapping[node_id_from_payload] = shortname
                self.logger.debug(
                    f"Mapped hardware ID {node_id_from_payload} to callsign "
                    f"{shortname} (from shortname)"
                )

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
        Process a telemetry message.

        Args:
            data: JSON data from Meshtastic
            numeric_node_id: Numeric node ID from the message
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
        """
        Process a traceroute message.

        Args:
            data: JSON data from Meshtastic
            numeric_node_id: Numeric node ID from the message
        """
        payload = data.get("payload")
        if not payload:
            self.logger.warning(
                f"Received traceroute message from {numeric_node_id} without payload"
            )
            return

        # Extract route information
        route = payload.get("route", [])

        self.logger.info(
            f"Traceroute from {sanitize_for_log(numeric_node_id)}: "
            f"Route={sanitize_for_log(route)}"
        )

    def _log_statistics(self) -> None:
        """Log current statistics."""
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
