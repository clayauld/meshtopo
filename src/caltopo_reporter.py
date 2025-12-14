"""
CalTopo API integration for sending position reports.
"""

import asyncio
import logging
import re
import secrets
from typing import Any, Optional
from urllib.parse import urlencode

import httpx


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
        # We will use an async client context manager in methods or a persistent one if
        # managed externally. For simplicity and resource management in this refactor,
        # we'll instantiate per request or use a shared client if we can manage its
        # lifecycle. Given the usage pattern, a shared client is better but requires
        # open/close management. We'll initialize it in a start method or just use a
        # context manager for each request if the frequency is low (which it is for
        # position updates). However, for efficiency, let's keep a client but we need
        # to ensure it's closed. For now, let's use a context manager per request to
        # be safe with lifecycle.
        self.timeout = 10  # seconds

    def _is_valid_caltopo_identifier(self, identifier: str) -> bool:
        """
        Validate that a CalTopo identifier (connect_key or group) is safe.

        Args:
            identifier: The identifier to validate

        Returns:
            bool: True if the identifier is valid, False otherwise
        """
        # Allow alphanumeric characters and underscores
        return bool(re.match(r"^[a-zA-Z0-9_]+$", identifier))

    def _validate_and_log_identifier(
        self, identifier: str, identifier_type: str
    ) -> bool:
        """
        Validate a CalTopo identifier and log an error if invalid.

        Args:
            identifier: The identifier to validate
            identifier_type: The type of identifier (e.g., 'connect_key', 'group')
                           for error logging

        Returns:
            bool: True if the identifier is valid, False otherwise
        """
        if not self._is_valid_caltopo_identifier(identifier):
            self.logger.error(f"Invalid CalTopo {identifier_type}: {identifier}")
            return False
        return True

    async def send_position_update(
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Send to connect_key endpoint if configured
            if self.config.caltopo.has_connect_key:
                total_attempts += 1
                if await self._send_to_connect_key(
                    client, callsign, latitude, longitude
                ):
                    success_count += 1

            # Send to group endpoint if configured
            if self.config.caltopo.has_group:
                total_attempts += 1
                group_to_use = group or self.config.caltopo.group
                if await self._send_to_group(
                    client, callsign, latitude, longitude, group_to_use
                ):
                    success_count += 1

        # Return True if at least one endpoint was successful
        return success_count > 0

    async def _send_to_connect_key(
        self,
        client: httpx.AsyncClient,
        callsign: str,
        latitude: float,
        longitude: float,
    ) -> bool:
        """Send position update to connect_key endpoint."""
        connect_key = self.config.caltopo.connect_key
        if not self._validate_and_log_identifier(connect_key, "connect_key"):
            return False

        url = f"{self.BASE_URL}/{connect_key}"
        params = {"id": callsign, "lat": latitude, "lng": longitude}
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return await self._make_api_request(client, full_url, callsign, "connect_key")

    async def _send_to_group(
        self,
        client: httpx.AsyncClient,
        callsign: str,
        latitude: float,
        longitude: float,
        group: str,
    ) -> bool:
        """Send position update to group endpoint."""
        if not self._validate_and_log_identifier(group, "group"):
            return False

        url = f"{self.BASE_URL}/{group}"
        params = {"id": callsign, "lat": latitude, "lng": longitude}
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        return await self._make_api_request(client, full_url, callsign, "group")

    async def _make_api_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        callsign: str,
        endpoint_type: str,
    ) -> bool:
        """Make an API request with retry logic."""
        max_retries = 3
        base_delay = 1.0  # seconds

        log_url = (
            re.sub(f"({self.BASE_URL}/)[^?]+", r"\1<REDACTED>", url)
            if endpoint_type == "connect_key"
            else url
        )

        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(
                    f"Sending position update for {callsign} to {endpoint_type} "
                    f"(attempt {attempt + 1}): {log_url}"
                )

                response = await client.get(url)

                if response.status_code == 200:
                    self.logger.info(
                        f"Successfully sent position update for {callsign} to "
                        f"{endpoint_type}"
                    )
                    return True
                elif 500 <= response.status_code < 600 or response.status_code == 429:
                    # Retry on server errors or rate limits
                    self.logger.warning(
                        f"CalTopo API error for {callsign} ({endpoint_type}): "
                        f"HTTP {response.status_code} - {response.text}. Retrying..."
                    )
                else:
                    # Don't retry on other client errors (e.g., 400, 401, 404)
                    self.logger.error(
                        f"CalTopo API error for {callsign} ({endpoint_type}): "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return False

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                self.logger.warning(
                    f"CalTopo API connection/timeout error for {callsign} "
                    f"({endpoint_type}): {e}. Retrying..."
                )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error sending position update for {callsign} "
                    f"({endpoint_type}): {e}"
                )
                return False

            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = (base_delay * (2**attempt)) + (
                    secrets.SystemRandom().uniform(0, 0.5)
                )
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

        self.logger.error(
            f"Failed to send position update for {callsign} ({endpoint_type}) "
            f"after {max_retries + 1} attempts"
        )
        return False

    async def test_connection(self) -> bool:
        """
        Test the connection to CalTopo API.

        Returns:
            bool: True if at least one endpoint connection test successful,
                False otherwise
        """
        success_count = 0
        total_attempts = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Test connect_key endpoint if configured
            if self.config.caltopo.has_connect_key:
                total_attempts += 1
                if await self._test_connect_key_endpoint(client):
                    success_count += 1

            # Test group endpoint if configured
            if self.config.caltopo.has_group:
                total_attempts += 1
                if await self._test_group_endpoint(client):
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

    async def _test_connect_key_endpoint(self, client: httpx.AsyncClient) -> bool:
        """Test connection to connect_key endpoint."""
        try:
            connect_key = self.config.caltopo.connect_key
            if not self._validate_and_log_identifier(connect_key, "connect_key"):
                return False

            test_url = (
                f"{self.BASE_URL}/{connect_key}" f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
            )
            response = await client.get(test_url)

            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(
                f"CalTopo connect_key endpoint test successful "
                f"(HTTP {response.status_code})"
            )
            return True
        except Exception as e:
            self.logger.error(f"CalTopo connect_key endpoint test failed: {e}")
            return False

    async def _test_group_endpoint(self, client: httpx.AsyncClient) -> bool:
        """Test connection to group endpoint."""
        try:
            group = self.config.caltopo.group
            if not self._validate_and_log_identifier(group, "group"):
                return False

            test_url = (
                f"{self.BASE_URL}/{group}" f"?id=MESHTOPO_SYSTEM_TEST&lat=0&lng=0"
            )
            response = await client.get(test_url)

            # Any response (even 4xx/5xx) means we can reach the API
            self.logger.info(
                f"CalTopo group endpoint test successful "
                f"(HTTP {response.status_code})"
            )
            return True
        except Exception as e:
            self.logger.error(f"CalTopo group endpoint test failed: {e}")
            return False

    async def close(self) -> None:
        """
        Close the reporter.
        No persistent session is maintained in this implementation.
        """
        pass
