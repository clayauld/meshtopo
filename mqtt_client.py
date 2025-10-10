"""
MQTT client for receiving Meshtastic position data.
"""

import json
import logging
import time
from typing import Callable, Optional, Dict, Any
import paho.mqtt.client as mqtt


class MqttClient:
    """
    MQTT client for connecting to broker and receiving Meshtastic data.
    """
    
    def __init__(self, config, message_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize MQTT client.
        
        Args:
            config: Configuration object containing MQTT settings
            message_callback: Function to call when a message is received
        """
        self.config = config
        self.message_callback = message_callback
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 1  # Start with 1 second delay
        
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = mqtt.Client()
            self.client.username_pw_set(
                self.config.mqtt.username, 
                self.config.mqtt.password
            )
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_log = self._on_log
            
            # Connect to broker
            self.logger.info(f"Connecting to MQTT broker at {self.config.mqtt.broker}:{self.config.mqtt.port}")
            self.client.connect(
                self.config.mqtt.broker, 
                self.config.mqtt.port, 
                keepalive=60
            )
            
            # Start the loop
            self.client.loop_start()
            
            # Wait for connection to be established
            timeout = 10  # seconds
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                self.logger.info("Successfully connected to MQTT broker")
                self.reconnect_attempts = 0
                return True
            else:
                self.logger.error("Failed to connect to MQTT broker within timeout")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.client:
            self.logger.info("Disconnecting from MQTT broker")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client connects to the broker.
        
        Args:
            client: The MQTT client instance
            userdata: User data passed to the client
            flags: Connection flags
            rc: Result code (0 = success)
        """
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
            
            # Subscribe to the configured topic
            topic = self.config.mqtt.topic
            result = client.subscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Subscribed to topic: {topic}")
            else:
                self.logger.error(f"Failed to subscribe to topic: {topic}")
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker. Result code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback for when the client disconnects from the broker.
        
        Args:
            client: The MQTT client instance
            userdata: User data passed to the client
            rc: Disconnect reason code
        """
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker. Reason code: {rc}")
            self._attempt_reconnect()
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback for when a message is received.
        
        Args:
            client: The MQTT client instance
            userdata: User data passed to the client
            msg: The received message
        """
        try:
            # Decode the message payload
            payload = msg.payload.decode('utf-8')
            self.logger.debug(f"Received message on topic {msg.topic}: {payload}")
            
            # Parse JSON
            data = json.loads(payload)
            
            # Call the message callback
            self.message_callback(data)
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON message: {e}. Payload: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _on_log(self, client, userdata, level, buf):
        """
        Callback for MQTT client logging.
        
        Args:
            client: The MQTT client instance
            userdata: User data passed to the client
            level: Log level
            buf: Log message
        """
        # Only log warnings and errors from paho-mqtt
        if level <= mqtt.MQTT_LOG_WARNING:
            self.logger.debug(f"MQTT: {buf}")
    
    def _attempt_reconnect(self) -> None:
        """
        Attempt to reconnect to the MQTT broker with exponential backoff.
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached. Giving up.")
            return
        
        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 60)  # Max 60 seconds
        
        self.logger.info(f"Attempting to reconnect in {delay} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        time.sleep(delay)
        
        try:
            if self.client:
                self.client.reconnect()
        except Exception as e:
            self.logger.error(f"Reconnection attempt failed: {e}")
            self._attempt_reconnect()
    
    def is_connected(self) -> bool:
        """
        Check if the client is connected to the broker.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected and self.client is not None
