"""
CalTopo API integration for sending position reports.
"""

import asyncio
import logging
import os
import random
import re
from typing import Any, Optional, cast
from urllib.parse import urlencode, urlparse

import httpx

from utils import sanitize_for_log


def _matches_url_pattern(url: str, pattern: str) -> bool:
    """
    Check if a URL matches a pattern with wildcard support.

    Args:
        url: The URL to check
        pattern: The pattern to match (supports * wildcard)

    Returns:
        bool: True if the URL matches the pattern
    """
    # Convert pattern to regex: escape special chars except *,
    # then replace * with .*
    pattern_regex = re.escape(pattern).replace(r"\*", ".*")
    return bool(re.match(f"^{pattern_regex}$", url))


class CalTopoReporter:
    """
    Asynchronous client for interfacing with the CalTopo Position Report API.

    This class handles the transmission of geographic position updates to
    CalTopo endpoints. It supports two primary modes of operation:

    1. **Personal Mode**: Individual 'connect_key' identifiers.
    2. **Team Mode**: Group-based reporting using 'group' identifiers.

    Features:

    - Robust networking with automatic retries and exponential backoff.
    - URL pattern validation for security and flexibility.
    - Sensitive information redaction in logs.
    - Support for shared HTTP clients to improve connection efficiency.
    """

    _raw_base_url = os.getenv(
        "CALTOPO_URL", "https://caltopo.com/api/v1/position/report"
    )
    _parsed_url = urlparse(_raw_base_url)

    # Allow explicit URL patterns for testing/development
    _allowed_patterns_str = os.getenv("CALTOPO_ALLOWED_URL_PATTERNS", "")
    _allowed_patterns = [
        p.strip() for p in _allowed_patterns_str.split(",") if p.strip()
    ]

    # Validate URL based on allowed patterns or production rules
    if _allowed_patterns:
        # Test/development mode: validate against explicit allowlist
        _url_matches = False
        for _pattern in _allowed_patterns:
            if _matches_url_pattern(_raw_base_url, _pattern):
                _url_matches = True
                break
        if not _url_matches:
            raise ValueError(
                f"Invalid CALTOPO_URL: {_raw_base_url}. "
                f"URL does not match any allowed pattern: "
                f"{', '.join(_allowed_patterns)}"
            )
    else:
        # Production mode: enforce that hostname must be caltopo.com
        if not (
            _parsed_url.hostname == "caltopo.com"
            or cast(str, _parsed_url.hostname).endswith(".caltopo.com")
        ):
            raise ValueError(
                f"Invalid CALTOPO_URL: {_raw_base_url}. "
                f"Hostname must be 'caltopo.com' or a subdomain thereof."
            )

    # Assign the validated URL to the class attribute
    BASE_URL = _raw_base_url

    def __init__(self, config: Any, client: Optional[httpx.AsyncClient] = None) -> None:
        """
        Initialize CalTopo reporter.

        Args:
            config: Configuration object containing CalTopo settings
            client: Optional shared httpx.AsyncClient. If not provided, a new client
                   will be created for each request.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Use a persistent client for efficiency (connection reuse)
        self.client = client
        self._owns_client = client is None
        self.timeout = 10  # seconds

    async def start(self) -> None:
        """Initialize the persistent HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            self._owns_client = True

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
            self.logger.error(
                f"Invalid CalTopo {identifier_type}: {sanitize_for_log(identifier)}"
            )
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
            bool: True if at least one endpoint (connect_key or group) was
                  successfully updated, False otherwise.
        """
        # Ensure client is initialized
        if self.client is None:
            await self.start()

        # We can safely assume client is not None after start(),
        # but type checker might complain
        # So we use a local variable or assert
        client = self.client
        if client is None:
            raise RuntimeError("httpx.AsyncClient failed to initialize")

        tasks = []

        # Send to connect_key endpoint if configured
        if self.config.caltopo.has_connect_key:
            tasks.append(
                self._send_to_connect_key(client, callsign, latitude, longitude)
            )

        # Send to group endpoint if configured
        if self.config.caltopo.has_group:
            group_to_use = group or self.config.caltopo.group
            tasks.append(
                self._send_to_group(client, callsign, latitude, longitude, group_to_use)
            )

        if not tasks:
            return False

        # Execute requests concurrently to reduce latency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)

        # Return True if at least one endpoint was successful
        return success_count > 0

    async def _send_to_connect_key(
        self,
        client: httpx.AsyncClient,
        callsign: str,
        latitude: float,
        longitude: float,
    ) -> bool:
        """
        Internal method to send position data to a personal connect_key endpoint.
        """
        connect_key = self.config.caltopo.connect_key
        # Safety check: ensure the key doesn't contain malicious characters
        # for URL construction.
        if not self._validate_and_log_identifier(connect_key, "connect_key"):
            return False

        # Construct specific endpoint URL
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
        """
        Internal method to send position data to a team 'group' endpoint.
        """
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
        """
        Execute an HTTP GET request to the CalTopo API with built-in retry logic.

        This method handles:
        - Exponential backoff with jitter for retries.
        - Redaction of sensitive keys in logs.
        - Differentiation between retryable (5xx, 429) and fatal (4xx) errors.

        Args:
            client: The async HTTP client to use.
            url: The fully constructed URL (including sensitive keys).
            callsign: The name/ID of the device being reported (for logging).
            endpoint_type: Category of endpoint ('connect_key' or 'group').

        Returns:
            bool: True if the request eventually succeeded (HTTP 200),
                  False if it failed after all retries or hit a fatal error.
        """
        max_retries = 3
        base_delay = 1.0  # seconds

        # Consistently redact sensitive path parameters for both endpoint types.
        log_url = re.sub(f"({self.BASE_URL}/)[^?]+", r"\1<REDACTED>", url)

        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(
                    f"Sending position update for {sanitize_for_log(callsign)} "
                    f"to {endpoint_type} (attempt {attempt + 1}): {log_url}"
                )

                response = await client.get(url)

                if response.status_code == 200:
                    self.logger.info(
                        f"Successfully sent position update for "
                        f"{sanitize_for_log(callsign)} to {endpoint_type}"
                    )
                    return True
                elif 500 <= response.status_code < 600 or response.status_code == 429:
                    # Retry on server errors or rate limits
                    self.logger.warning(
                        f"CalTopo API error for {sanitize_for_log(callsign)} "
                        f"({endpoint_type}): HTTP {response.status_code} - "
                        f"{sanitize_for_log(response.text)}. Retrying..."
                    )
                else:
                    # Don't retry on other client errors (e.g., 400, 401, 404)
                    self.logger.error(
                        f"CalTopo API error for {sanitize_for_log(callsign)} "
                        f"({endpoint_type}): HTTP {response.status_code} - "
                        f"{sanitize_for_log(response.text)}"
                    )
                    return False

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                self.logger.warning(
                    f"CalTopo API connection/timeout error for "
                    f"{sanitize_for_log(callsign)} ({endpoint_type}): {e}. Retrying..."
                )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error sending position update for "
                    f"{sanitize_for_log(callsign)} ({endpoint_type}): {e}"
                )
                return False

            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = (base_delay * (2**attempt)) + (
                    random.SystemRandom().uniform(0, 0.5)
                )
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

        self.logger.error(
            f"Failed to send position update for {sanitize_for_log(callsign)} "
            f"({endpoint_type}) after {max_retries + 1} attempts"
        )
        return False

    async def test_connection(self) -> bool:
        """
        Test the connection to CalTopo API.

        Returns:
            bool: True if at least one endpoint connection test successful,
                False otherwise
        """
        # Ensure client is initialized
        if self.client is None:
            await self.start()

        client = self.client
        if client is None:
            raise RuntimeError("httpx.AsyncClient failed to initialize")

        tasks = []

        # Test connect_key endpoint if configured
        if self.config.caltopo.has_connect_key:
            tasks.append(self._test_connect_key_endpoint(client))

        # Test group endpoint if configured
        if self.config.caltopo.has_group:
            tasks.append(self._test_group_endpoint(client))

        if not tasks:
            return False

        # Run tests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception) and r)
        total_attempts = len(tasks)

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
        Close the reporter and the underlying HTTP client.
        """
        if self.client and self._owns_client:
            await self.client.aclose()
            self.client = None
