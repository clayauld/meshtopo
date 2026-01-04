# Module `caltopo_reporter`

CalTopo Reporting Module.

This module is responsible for the egress of location data to the CalTopo API.
It handles:

1. **Connection Management:** Using a shared `httpx.AsyncClient` for connection
    pooling.
2. **Reliability:** Implementing exponential backoff and retry logic for network
    failures.
3. **Concurrency:** Sending updates to multiple endpoints (e.g., legacy connect keys
    and new groups) in parallel.
4. **Security:** Ensuring all traffic is HTTPS.

## Usage

    reporter = CalTopoReporter(config, client)
    await reporter.start()
    await reporter.send_position_update("User A", 34.0, -118.0)
    await reporter.close()

## Classes

## `class CalTopoReporter`

Handles secure and reliable communication with the CalTopo API.

This class encapsulates the logic for sending position updates to CalTopo.
It supports both the legacy "Connect Key" API and the newer "Group" API.

Attributes:
    config (Config): The application configuration.
    client (httpx.AsyncClient): The shared HTTP client.
    base_url (str): The base URL for the CalTopo API.

### `def __init__(self, config: config.config.Config, client: Optional[httpx.AsyncClient] = None)`

Initialize the reporter.

Args:
    config: Application configuration.
    client: Optional shared httpx client. If not provided, one is created.

### `def close(self) -> None`

Close resources.

Closes the HTTP client if it was created by this instance.

### `def send_position_update(self, callsign: str, lat: float, lon: float, group: Optional[str] = None) -> bool`

Send a position update to CalTopo.

This method handles the complexity of sending to multiple configured destinations
(e.g., a global connect key and a specific group) concurrently.

Args:
    callsign: The display name of the user.
    lat: Latitude in decimal degrees.
    lon: Longitude in decimal degrees.
    group: Optional specific group to send to (overrides config if logic requires).

Returns:
    bool: True if at least one update succeeded, False if all failed.

### `def start(self) -> None`

Prepare the reporter for use.

(Currently a placeholder for any async setup logic).

### `def test_connection(self) -> bool`

Verify connectivity to the CalTopo API.

Sends a test request to ensure the endpoint is reachable.

Returns:
    bool: True if reachable, False otherwise.

## Functions

## `def _validate_caltopo_url(url: str) -> None`

Validate that the CALTOPO_API_URL is safe.
Must be caltopo.com or a subdomain, unless strictly overridden.
