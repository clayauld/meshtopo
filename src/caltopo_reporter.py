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
            bool: True if successful, False otherwise
        """
        # Build the API URL
        url = self._build_api_url(callsign, latitude, longitude, group)

        try:
            self.logger.debug(
                f"Sending position update for {callsign}: " f"{latitude}, {longitude}"
            )

            # Make the HTTP GET request
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                self.logger.info(f"Successfully sent position update for {callsign}")
                return True
            else:
                self.logger.error(
                    f"CalTopo API error for {callsign}: "
                    f"HTTP {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            self.logger.error(f"CalTopo API timeout for {callsign}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"CalTopo API connection error for {callsign}")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"CalTopo API request error for {callsign}: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error sending position update for " f"{callsign}: {e}"
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

        Args:
            callsign: Device callsign/identifier
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            group: Optional GROUP for group-based API mode

        Returns:
            str: Complete API URL
        """
        # Determine API mode and construct URL accordingly
        if self.config.caltopo.api_mode == "group":
            # Group-based API mode
            if not group:
                raise ValueError("GROUP is required for group-based API mode")
            url = f"{self.BASE_URL}/{group}"
        else:
            # Connect key API mode (default)
            url = f"{self.BASE_URL}/{self.config.caltopo.connect_key}"

        # Build query parameters
        params = {"id": callsign, "lat": latitude, "lng": longitude}

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
            if self.config.caltopo.api_mode == "group":
                # Group-based API mode - use global group
                if not self.config.caltopo.group:
                    self.logger.error(
                        "Cannot test group-based API without global group configured"
                    )
                    return False
                test_url = (
                    f"{self.BASE_URL}/{self.config.caltopo.group}"
                    f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
                )
            else:
                # Connect key API mode
                test_url = (
                    f"{self.BASE_URL}/{self.config.caltopo.connect_key}"
                    f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
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

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.logger.debug("CalTopo reporter session closed")
