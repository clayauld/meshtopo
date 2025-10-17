"""
CalTopo API integration for sending position reports.
"""

import logging
from typing import Any, Optional
from urllib.parse import urlencode

import requests


class CalTopoReporter:
    """
    Handles communication with the CalTopo Position Report API.
    """

    BASE_URL = "https://caltopo.com/api/v1/position/report"

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

    def send_position_update(
        self,
        callsign: str,
        latitude: float,
        longitude: float,
        group: Optional[str] = None,
    ) -> bool:
        """
        Send a position update to CalTopo.

        Args:
            callsign: Device callsign/identifier
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            group: Optional GROUP for group-based API mode

        Returns:
            bool: True if at least one endpoint was successful, False otherwise
        """
        success_count = 0
        total_attempts = 0

        # Send to connect_key endpoint if configured
        if self.config.caltopo.has_connect_key:
            total_attempts += 1
            if self._send_to_connect_key(callsign, latitude, longitude):
                success_count += 1

        # Send to group endpoint if configured
        if self.config.caltopo.has_group:
            total_attempts += 1
            group_to_use = group or self.config.caltopo.group
            if self._send_to_group(callsign, latitude, longitude, group_to_use):
                success_count += 1

        # Return True if at least one endpoint was successful
        return success_count > 0

    def _validate_endpoint(self, endpoint: Optional[str], endpoint_type: str) -> bool:
        """Validate that an endpoint is configured."""
        if not endpoint:
            self.logger.error(f"CalTopo {endpoint_type} is not configured")
            return False
        return True

    def _send_to_connect_key(
        self,
        callsign: str,
        latitude: float,
        longitude: float,
    ) -> bool:
        """Send position update to connect_key endpoint."""
        if not self._validate_endpoint(self.config.caltopo.connect_key, "connect_key"):
            return False

        url = f"{self.BASE_URL}/{self.config.caltopo.connect_key}"
        params = {"id": callsign, "lat": latitude, "lng": longitude}
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return self._make_api_request(full_url, callsign, "connect_key")

    def _send_to_group(
        self,
        callsign: str,
        latitude: float,
        longitude: float,
        group: Optional[str],
    ) -> bool:
        """Send position update to group endpoint."""
        if not self._validate_endpoint(group, "group"):
            return False

        url = f"{self.BASE_URL}/{group}"
        params = {"id": callsign, "lat": latitude, "lng": longitude}
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return self._make_api_request(full_url, callsign, "group")

    def _make_api_request(self, url: str, callsign: str, endpoint_type: str) -> bool:
        """Make an API request and handle the response."""
        try:
            self.logger.debug(
                f"Sending position update for {callsign} to {endpoint_type}: " f"{url}"
            )

            # Make the HTTP GET request
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                self.logger.info(
                    f"Successfully sent position update for {callsign} to "
                    f"{endpoint_type}"
                )
                return True
            else:
                self.logger.error(
                    f"CalTopo API error for {callsign} ({endpoint_type}): "
                    f"HTTP {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            self.logger.error(f"CalTopo API timeout for {callsign} ({endpoint_type})")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(
                f"CalTopo API connection error for {callsign} ({endpoint_type})"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"CalTopo API request error for {callsign} ({endpoint_type}): {e}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error sending position update for {callsign} "
                f"({endpoint_type}): {e}"
            )
            return False

    def _build_api_url(
        self,
        callsign: str,
        latitude: float,
        longitude: float,
        group: Optional[str] = None,
    ) -> str:
        """
        Build the CalTopo API URL with query parameters.

        This method is kept for backward compatibility but is deprecated.
        Use the new _send_to_connect_key and _send_to_group methods instead.

        Args:
            callsign: Device callsign/identifier
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            group: Optional GROUP for group-based API mode

        Returns:
            str: Complete API URL
        """
        # For backward compatibility, prefer connect_key if available
        if self.config.caltopo.has_connect_key:
            url = f"{self.BASE_URL}/{self.config.caltopo.connect_key}"
        elif self.config.caltopo.has_group:
            group_to_use = group or self.config.caltopo.group
            if not group_to_use:
                raise ValueError("GROUP is required for group-based API mode")
            url = f"{self.BASE_URL}/{group_to_use}"
        else:
            raise ValueError("No CalTopo endpoint configured")

        # Build query parameters
        params = {"id": callsign, "lat": latitude, "lng": longitude}

        # Encode parameters and append to URL
        query_string = urlencode(params)
        return f"{url}?{query_string}"

    def test_connection(self) -> bool:
        """
        Test the connection to CalTopo API.

        Returns:
            bool: True if at least one endpoint connection test successful,
                False otherwise
        """
        success_count = 0
        total_attempts = 0

        # Test connect_key endpoint if configured
        if self.config.caltopo.has_connect_key:
            total_attempts += 1
            if self._test_connect_key_endpoint():
                success_count += 1

        # Test group endpoint if configured
        if self.config.caltopo.has_group:
            total_attempts += 1
            if self._test_group_endpoint():
                success_count += 1

        if success_count > 0:
            self.logger.info(
                f"CalTopo API connectivity test successful "
                f"({success_count}/{total_attempts} endpoints)"
            )
            return True
        else:
            self.logger.error("CalTopo API connectivity test failed for all endpoints")
            return False

    def _test_connect_key_endpoint(self) -> bool:
        """Test connection to connect_key endpoint."""
        if not self._validate_endpoint(self.config.caltopo.connect_key, "connect_key"):
            return False
        try:
            test_url = (
                f"{self.BASE_URL}/{self.config.caltopo.connect_key}"
                f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
            )
            response = self.session.get(test_url, timeout=self.timeout)

            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(
                f"CalTopo connect_key endpoint test successful "
                f"(HTTP {response.status_code})"
            )
            return True
        except Exception as e:
            self.logger.error(f"CalTopo connect_key endpoint test failed: {e}")
            return False

    def _test_group_endpoint(self) -> bool:
        """Test connection to group endpoint."""
        if not self._validate_endpoint(self.config.caltopo.group, "group"):
            return False
        try:
            test_url = (
                f"{self.BASE_URL}/{self.config.caltopo.group}"
                f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
            )
            response = self.session.get(test_url, timeout=self.timeout)

            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(
                f"CalTopo group endpoint test successful "
                f"(HTTP {response.status_code})"
            )
            return True
        except Exception as e:
            self.logger.error(f"CalTopo group endpoint test failed: {e}")
            return False

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.logger.debug("CalTopo reporter session closed")
