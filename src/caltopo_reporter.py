"""
CalTopo API integration for sending position reports and Team API management.
"""

import logging
import base64
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests


class CalTopoReporter:
    """
    Handles communication with the CalTopo Position Report API and Team API.
    """

    BASE_URL = "https://caltopo.com/api/v1/position/report"
    TEAM_API_URL = "https://caltopo.com/api/v1/team"

    def __init__(self, config: Any) -> None:
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

        # Set up Team API authentication if enabled
        self.team_api_auth_header = None
        if config.caltopo.team_api.enabled:
            self._setup_team_api_auth()

    def _setup_team_api_auth(self) -> None:
        """Set up authentication headers for Team API."""
        try:
            credential_id = self.config.caltopo.team_api.credential_id
            secret_key = self.config.caltopo.team_api.secret_key

            if not credential_id or not secret_key:
                self.logger.warning("CalTopo Team API credentials not configured")
                return

            # Create basic auth header
            credentials = f"{credential_id}:{secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.team_api_auth_header = f"Basic {encoded_credentials}"

            self.logger.info("CalTopo Team API authentication configured")

        except Exception as e:
            self.logger.error(f"Failed to setup CalTopo Team API authentication: {e}")

    def send_position_update(
        self, node_id: str, latitude: float, longitude: float
    ) -> bool:
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
            self.logger.debug(
                f"Sending position update for {node_id} -> {device_id}: "
                f"{latitude}, {longitude}"
            )

            # Make the HTTP GET request
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                self.logger.info(
                    f"Successfully sent position update for {node_id} -> {device_id}"
                )
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
            self.logger.error(
                f"CalTopo API connection error for {node_id} -> {device_id}"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"CalTopo API request error for {node_id} -> {device_id}: {e}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error sending position update for "
                f"{node_id} -> {device_id}: {e}"
            )
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
        params = {"id": device_id, "lat": latitude, "lng": longitude}

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
            # We'll use a dummy position that should be rejected but still
            # test connectivity
            test_url = (
                f"{self.BASE_URL}/{self.config.caltopo.group}" f"?id=TEST&lat=0&lng=0"
            )

            response = self.session.get(test_url, timeout=self.timeout)

            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(
                f"CalTopo API connectivity test successful "
                f"(HTTP {response.status_code})"
            )
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"CalTopo API connectivity test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error during CalTopo API connectivity test: {e}"
            )
            return False

    # Team API methods
    def list_maps(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available CalTopo maps via Team API.

        Returns:
            list: List of map information dictionaries
        """
        try:
            if not self.config.caltopo.team_api.enabled:
                self.logger.warning("CalTopo Team API not enabled")
                return []

            if not self.team_api_auth_header:
                self.logger.error("CalTopo Team API not authenticated")
                return []

            headers = {"Authorization": self.team_api_auth_header}
            response = self.session.get(
                f"{self.TEAM_API_URL}/maps",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                maps_data = response.json()
                self.logger.info(f"Retrieved {len(maps_data)} maps from CalTopo Team API")
                return maps_data
            else:
                self.logger.error(f"Failed to list maps: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            self.logger.error(f"Error listing CalTopo maps: {e}")
            return []

    def get_map_details(self, map_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific map via Team API.

        Args:
            map_id: CalTopo map identifier

        Returns:
            dict: Map details or None if not found
        """
        try:
            if not self.config.caltopo.team_api.enabled:
                self.logger.warning("CalTopo Team API not enabled")
                return None

            if not self.team_api_auth_header:
                self.logger.error("CalTopo Team API not authenticated")
                return None

            headers = {"Authorization": self.team_api_auth_header}
            response = self.session.get(
                f"{self.TEAM_API_URL}/maps/{map_id}",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                map_details = response.json()
                self.logger.info(f"Retrieved details for map {map_id}")
                return map_details
            elif response.status_code == 404:
                self.logger.warning(f"Map {map_id} not found")
                return None
            else:
                self.logger.error(f"Failed to get map details: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting map details for {map_id}: {e}")
            return None

    def test_map_connection(self, map_id: str) -> bool:
        """
        Test connection to a specific map via Team API.

        Args:
            map_id: CalTopo map identifier

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not self.config.caltopo.team_api.enabled:
                self.logger.warning("CalTopo Team API not enabled")
                return False

            if not self.team_api_auth_header:
                self.logger.error("CalTopo Team API not authenticated")
                return False

            headers = {"Authorization": self.team_api_auth_header}
            response = self.session.get(
                f"{self.TEAM_API_URL}/maps/{map_id}/test",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                self.logger.info(f"Map {map_id} connection test passed")
                return True
            else:
                self.logger.error(f"Map {map_id} connection test failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error testing map connection for {map_id}: {e}")
            return False

    def get_team_info(self) -> Optional[Dict[str, Any]]:
        """
        Get team information via Team API.

        Returns:
            dict: Team information or None if failed
        """
        try:
            if not self.config.caltopo.team_api.enabled:
                self.logger.warning("CalTopo Team API not enabled")
                return None

            if not self.team_api_auth_header:
                self.logger.error("CalTopo Team API not authenticated")
                return None

            headers = {"Authorization": self.team_api_auth_header}
            response = self.session.get(
                f"{self.TEAM_API_URL}/info",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                team_info = response.json()
                self.logger.info("Retrieved team information")
                return team_info
            else:
                self.logger.error(f"Failed to get team info: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting team info: {e}")
            return None

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.logger.debug("CalTopo reporter session closed")
