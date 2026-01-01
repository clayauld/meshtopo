<!-- markdownlint-disable-file MD046 -->

# Module `caltopo_reporter`

CalTopo API Integration Module

This module handles all HTTP communication with the CalTopo Position Reporting API.
It is designed for robustness and performance using modern asynchronous patterns.

## Architecture

* **HTTP Client Reuse:** The `CalTopoReporter` utilizes a shared `httpx.AsyncClient`
    passed from `GatewayApp`. This enables persistent connection pooling (Keep-Alive),
    significantly reducing latency for frequent position updates.
* **Security:**
  * **URL Whitelisting:** The base URL is strictly validated against allowed domains
        (defaulting to `*.caltopo.com`) to prevent SSRF (Server-Side Request Forgery)
        attacks.
  * **Log Sanitization:** Sensitive path parameters (like the `connect_key`) are
        redacted from logs.
  * **Input Validation:** Identifiers are validated to ensure they are alphanumeric.
* **Resilience:**
  * **Exponential Backoff:** The `_make_api_request` method implements a retry
        loop with jittered exponential backoff. This handles transient network
        failures (5xx, 429) gracefully without thundering herd problems.
  * **Concurrent Requests:** The `send_position_update` method uses
        `asyncio.gather` to send updates to multiple endpoints (e.g., both a private
        Connect Key map and a public Group map) in parallel.

## Usage

This class is typically instantiated once by the `GatewayApp` and remains active for
the application lifecycle. It requires an initialized `Config` object and an
`httpx.AsyncClient`.

## Classes

## `class CalTopoReporter`

Handles secure and reliable communication with the CalTopo API.

### `def __init__(self, config: Any, client: Optional[httpx.AsyncClient] = None) -> None`

Initialize CalTopo reporter.

Args:
    config: Configuration object containing CalTopo settings
    client: Shared httpx.AsyncClient (recommended). If None, one will
            be created.

### `def close(self) -> None`

Close the reporter resources.
Only closes the client if we own it.

### `def send_position_update(self, callsign: str, latitude: float, longitude: float, group: Optional[str] = None) -> bool`

Send a position update to CalTopo.

This method will broadcast the update to all configured endpoints (Connect Key
and/or Group) concurrently.

Returns:
    bool: True if at least one endpoint accepted the update.

### `def start(self) -> None`

Initialize the HTTP client if one was not provided.
Called by `GatewayApp.initialize`.

### `def test_connection(self) -> bool`

Test the connection to CalTopo API by sending a dummy request.
Used during startup to verify configuration.

## Functions

## `def _matches_url_pattern(url: str, pattern: str) -> bool`

Check if a URL matches a pattern with wildcard support.
Helper for security validation.
