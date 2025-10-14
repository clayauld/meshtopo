"""
Main gateway application that orchestrates MQTT and CalTopo communication.
"""

import logging
import signal
import sys
import time
from typing import Any, Dict, Optional, Union

from caltopo_reporter import CalTopoReporter
from config.config import Config
from mqtt_client import MqttClient


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
        self.running = False
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats: Dict[str, Union[int, float]] = {
            "messages_received": 0,
            "messages_processed": 0,
            "position_updates_sent": 0,
            "errors": 0,
            "start_time": 0.0,
        }

        # Node ID mapping: numeric ID -> hardware ID -> callsign
        self.node_id_mapping: Dict[str, str] = {}
        self.callsign_mapping: Dict[str, str] = {}  # hardware_id -> callsign
        self.configured_devices: set = (
            set()
        )  # Track which devices are in the nodes config

    def initialize(self) -> bool:
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

            # Check if we should use internal MQTT broker
            if self.config.mqtt.use_internal_broker:
                self.logger.info("Using internal MQTT broker")
                # Update broker hostname to use internal service name
                self.config.mqtt.broker = "mosquitto"

            # Initialize CalTopo reporter
            self.logger.info("Initializing CalTopo reporter...")
            self.caltopo_reporter = CalTopoReporter(self.config)

            # Test CalTopo connectivity
            if not self.caltopo_reporter.test_connection():
                self.logger.warning(
                    "CalTopo API connectivity test failed, but continuing..."
                )

            # Initialize MQTT client
            self.logger.info("Initializing MQTT client...")
            self.mqtt_client = MqttClient(self.config, self._process_message)

            # Build set of configured devices for tracking
            self.configured_devices = set(self.config.nodes.keys())
            self.logger.info(f"Configured devices: {self.configured_devices}")

            self.logger.info("Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def start(self) -> None:
        """
        Start the gateway service.
        """
        if not self.initialize():
            self.logger.error("Failed to initialize application. Exiting.")
            sys.exit(1)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("Starting Meshtopo gateway service...")
        self.running = True
        self.stats["start_time"] = time.time()

        # Connect to MQTT broker
        if self.mqtt_client is None:
            self.logger.error("MQTT client not initialized. Exiting.")
            sys.exit(1)

        if not self.mqtt_client.connect():
            self.logger.error("Failed to connect to MQTT broker. Exiting.")
            sys.exit(1)

        self.logger.info("Gateway service started successfully")

        try:
            # Main loop
            while self.running:
                time.sleep(1)

                # Log statistics every 60 seconds
                if (
                    self.stats["start_time"]
                    and (time.time() - self.stats["start_time"]) % 60 < 1
                ):
                    self._log_statistics()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop the gateway service gracefully.
        """
        if not self.running:
            return

        self.logger.info("Stopping gateway service...")
        self.running = False

        # Disconnect MQTT client
        if self.mqtt_client:
            self.mqtt_client.disconnect()

        # Close CalTopo reporter
        if self.caltopo_reporter:
            self.caltopo_reporter.close()

        # Log final statistics
        self._log_statistics()
        self.logger.info("Gateway service stopped")

    def _process_message(self, data: Dict[str, Any]) -> None:
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
                self._process_position_message(data, numeric_node_id)
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

    def _process_position_message(
        self, data: Dict[str, Any], numeric_node_id: str
    ) -> None:
        """
        Process a position message.

        Args:
            data: JSON data from Meshtastic
            numeric_node_id: Numeric node ID from the message
        """
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
        if not hardware_id:
            # Try to use sender field as fallback (contains hardware ID)
            sender = data.get("sender")
            if sender and sender.startswith("!"):
                # Validate that sender is a string
                if not isinstance(sender, str):
                    self.logger.error(
                        f"Invalid sender type: expected string, got {type(sender)}"
                    )
                    self.stats["errors"] += 1
                    return
                hardware_id = sender
                # Build the mapping for future use
                self.node_id_mapping[str(numeric_node_id)] = hardware_id
                self.logger.debug(
                    f"Built mapping from sender field: {numeric_node_id} -> "
                    f"{hardware_id}"
                )
            else:
                self.logger.warning(
                    f"No hardware ID mapping found for numeric node ID "
                    f"{numeric_node_id}. Position update will be skipped until "
                    f"nodeinfo message is received."
                )
                return

        # Get callsign for this hardware ID
        callsign = self.callsign_mapping.get(hardware_id)
        if not callsign:
            # Check if we have a configured device_id for this hardware ID
            if self.config is None:
                self.logger.error("Configuration not loaded")
                self.stats["errors"] += 1
                return
            configured_device_id = self.config.get_node_device_id(hardware_id)
            if configured_device_id:
                callsign = configured_device_id
                self.callsign_mapping[hardware_id] = callsign
                self.logger.debug(
                    f"Using configured device_id as callsign: "
                    f"{hardware_id} -> {callsign}"
                )
            else:
                # Check if this is an unknown device and if we should allow it
                is_unknown_device = hardware_id not in self.configured_devices
                if is_unknown_device and not self.config.devices.allow_unknown_devices:
                    self.logger.warning(
                        f"Unknown device {hardware_id} position update blocked "
                        f"(allow_unknown_devices=False). Device is tracked but no "
                        f"position sent."
                    )
                    return
                elif is_unknown_device and self.config.devices.allow_unknown_devices:
                    # Allow unknown device but use hardware_id as callsign
                    callsign = hardware_id
                    self.callsign_mapping[hardware_id] = callsign
                    self.logger.info(
                        f"Allowing unknown device {hardware_id} "
                        f"(allow_unknown_devices=True). Using hardware_id as callsign."
                    )
                else:
                    # Known device but no callsign mapping - this shouldn't happen
                    self.logger.warning(
                        f"No callsign mapping found for known hardware ID "
                        f"{hardware_id}. Position update will be skipped until "
                        f"nodeinfo message is received."
                    )
                    return

        # Get GROUP for this device (if using group-based API)
        group = None
        if self.config is not None and self.config.caltopo.api_mode == "group":
            group = self.config.get_node_group(hardware_id)

        success = self.caltopo_reporter.send_position_update(
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
            f"Node info from {numeric_node_id}: ID={node_id_from_payload}, "
            f"Name={longname} ({shortname}), Hardware={hardware}, Role={role}"
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
            f"Telemetry from {numeric_node_id}: Battery={battery_level}%, "
            f"Voltage={voltage}V, Uptime={uptime_seconds}s, "
            f"Air util TX={air_util_tx}, Channel util={channel_utilization}%"
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

        self.logger.info(f"Traceroute from {numeric_node_id}: Route={route}")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        self.logger.info(
            f"Received signal {signal_name}, initiating graceful shutdown..."
        )
        self.stop()
        sys.exit(0)

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
