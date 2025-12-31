"""
CalTopo API Integration Module

This module handles all HTTP communication with the CalTopo Position Reporting API.
It is designed for robustness and performance using modern asynchronous patterns.

## Architecture

*   **HTTP Client Reuse:** The `CalTopoReporter` utilizes a shared `httpx.AsyncClient`
    passed from `GatewayApp`. This enables persistent connection pooling (Keep-Alive),
    significantly reducing latency for frequent position updates.
*   **Security:**
    *   **URL Whitelisting:** The base URL is strictly validated against allowed domains
        (defaulting to `*.caltopo.com`) to prevent SSRF (Server-Side Request Forgery)
        attacks.
    *   **Log Sanitization:** Sensitive path parameters (like the `connect_key`) are
        redacted from logs.
    *   **Input Validation:** Identifiers are validated to ensure they are alphanumeric.
*   **Resilience:**
    *   **Exponential Backoff:** The `_make_api_request` method implements a retry
        loop with jittered exponential backoff. This handles transient network
        failures (5xx, 429) gracefully without thundering herd problems.
    *   **Concurrent Requests:** The `send_position_update` method uses
        `asyncio.gather` to send updates to multiple endpoints (e.g., both a private
        Connect Key map and a public Group map) in parallel.

## Usage

This class is typically instantiated once by the `GatewayApp` and remains active for
the application lifecycle. It requires an initialized `Config` object and an
`httpx.AsyncClient`.
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
    Helper for security validation.
    """
    # Convert pattern to regex: escape special chars except *,
    # then replace * with .*
    pattern_regex = re.escape(pattern).replace(r"\*", ".*")
    return bool(re.match(f"^{pattern_regex}$", url))


class CalTopoReporter:
    """
    Handles secure and reliable communication with the CalTopo API.
    """

    _raw_base_url = os.getenv(
        "CALTOPO_URL", "https://caltopo.com/api/v1/position/report"
    )
    _parsed_url = urlparse(_raw_base_url)

    # Security: Allow explicit URL patterns for testing/development
    _allowed_patterns_str = os.getenv("CALTOPO_ALLOWED_URL_PATTERNS", "")
    _allowed_patterns = [
        p.strip() for p in _allowed_patterns_str.split(",") if p.strip()
    ]

    # Security: Validate URL based on allowed patterns or production rules
    # This block executes at module load time to fail fast on invalid config.
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
            client: Shared httpx.AsyncClient (recommended). If None, one will
                    be created.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Use a persistent client for efficiency (connection reuse)
        self.client = client
        self._owns_client = client is None
        self.timeout = 10  # seconds

    async def start(self) -> None:
        """
        Initialize the HTTP client if one was not provided.
        Called by `GatewayApp.initialize`.
        """
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            self._owns_client = True

    def _is_valid_caltopo_identifier(self, identifier: str) -> bool:
        """
        Security: Validate that a CalTopo identifier (connect_key or group) is safe.
        Strictly alphanumeric to prevent injection.
        """
        return bool(re.match(r"^[a-zA-Z0-9_]+$", identifier))

    def _validate_and_log_identifier(
        self, identifier: str, identifier_type: str
    ) -> bool:
        """
        Validate a CalTopo identifier and log an error if invalid.
        """
        if not self._is_valid_caltopo_identifier(identifier):
            self.logger.error(
                f"Invalid CalTopo {identifier_type}: " f"{sanitize_for_log(identifier)}"
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

        This method will broadcast the update to all configured endpoints (Connect Key
        and/or Group) concurrently.

        Returns:
            bool: True if at least one endpoint accepted the update.
        """
        # Ensure client is initialized
        if self.client is None:
            await self.start()

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

        # Execute requests concurrently to reduce latency using gather
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
        """Helper to send position update to connect_key endpoint."""
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
        """Helper to send position update to group endpoint."""
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
        Make an API request with retry logic and exponential backoff.

        This is the core network reliability layer.

        Logic:
        1.  Attempt request.
        2.  If 200 OK -> Success.
        3.  If 5xx or 429 -> Retry with backoff.
        4.  If other 4xx -> Fail (client error).
        5.  Backoff includes Jitter to prevent thundering herd.
        """
        max_retries = 3
        base_delay = 1.0  # seconds

        # Security: Consistently redact sensitive path parameters for both endpoint
        # types.
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
        Test the connection to CalTopo API by sending a dummy request.
        Used during startup to verify configuration.
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
        Close the reporter resources.
        Only closes the client if we own it.
        """
        if self.client and self._owns_client:
            await self.client.aclose()
            self.client = None
