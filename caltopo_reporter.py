"""
CalTopo API integration for sending position reports.
"""

import logging
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode


class CalTopoReporter:
    """
    Handles communication with the CalTopo Position Report API.
    """
    
    BASE_URL = "https://caltopo.com/api/v1/position/report"
    
    def __init__(self, config):
        """
        Initialize CalTopo reporter.
        
        Args:
            config: Configuration object containing CalTopo settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set a reasonable timeout for API requests
        self.timeout = 10  # seconds
    
    def send_position_update(self, node_id: str, latitude: float, longitude: float) -> bool:
        """
        Send a position update to CalTopo.
        
        Args:
            node_id: Meshtastic node ID
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the CalTopo device ID for this node
        device_id = self.config.get_node_device_id(node_id)
        if not device_id:
            self.logger.debug(f"No device mapping found for node {node_id}")
            return False
        
        # Build the API URL
        url = self._build_api_url(device_id, latitude, longitude)
        
        try:
            self.logger.debug(f"Sending position update for {node_id} -> {device_id}: {latitude}, {longitude}")
            
            # Make the HTTP GET request
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent position update for {node_id} -> {device_id}")
                return True
            else:
                self.logger.error(
                    f"CalTopo API error for {node_id} -> {device_id}: "
                    f"HTTP {response.status_code} - {response.text}"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"CalTopo API timeout for {node_id} -> {device_id}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"CalTopo API connection error for {node_id} -> {device_id}")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"CalTopo API request error for {node_id} -> {device_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending position update for {node_id} -> {device_id}: {e}")
            return False
    
    def _build_api_url(self, device_id: str, latitude: float, longitude: float) -> str:
        """
        Build the CalTopo API URL with query parameters.
        
        Args:
            device_id: CalTopo device ID
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            str: Complete API URL
        """
        # Construct the base URL with group
        url = f"{self.BASE_URL}/{self.config.caltopo.group}"
        
        # Build query parameters
        params = {
            'id': device_id,
            'lat': latitude,
            'lng': longitude
        }
        
        # Encode parameters and append to URL
        query_string = urlencode(params)
        return f"{url}?{query_string}"
    
    def test_connection(self) -> bool:
        """
        Test the connection to CalTopo API.
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            # Try to make a simple request to test connectivity
            # We'll use a dummy position that should be rejected but still test connectivity
            test_url = f"{self.BASE_URL}/{self.config.caltopo.group}?id=TEST&lat=0&lng=0"
            
            response = self.session.get(test_url, timeout=self.timeout)
            
            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(f"CalTopo API connectivity test successful (HTTP {response.status_code})")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"CalTopo API connectivity test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during CalTopo API connectivity test: {e}")
            return False
    
    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.logger.debug("CalTopo reporter session closed")
