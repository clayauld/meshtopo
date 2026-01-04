# Module `caltopo_reporter`

CalTopo API integration for sending position reports.

## Classes

## `class CalTopoReporter`

Handles communication with the CalTopo Position Report API.

### `def __init__(self, config: Any, client: Optional[httpx.AsyncClient] = None) -> None`

Initialize CalTopo reporter.

Args:
    config: Configuration object containing CalTopo settings
    client: Optional shared httpx.AsyncClient. If not provided, a new client
           will be created for each request.

### `def close(self) -> None`

Close the reporter and the underlying HTTP client.

### `def send_position_update(self, callsign: str, latitude: float, longitude: float, group: Optional[str] = None) -> bool`

Send a position update to CalTopo.

Args:
    callsign: Device callsign/identifier
    latitude: Latitude in decimal degrees
    longitude: Longitude in decimal degrees
    group: Optional GROUP for group-based API mode

Returns:
    bool: True if at least one endpoint was successful, False otherwise

### `def start(self) -> None`

Initialize the persistent HTTP client.

### `def test_connection(self) -> bool`

Test the connection to CalTopo API.

Returns:
    bool: True if at least one endpoint connection test successful,
        False otherwise

## Functions

## `def _matches_url_pattern(url: str, pattern: str) -> bool`

Check if a URL matches a pattern with wildcard support.

Args:
    url: The URL to check
    pattern: The pattern to match (supports * wildcard)

Returns:
    bool: True if the URL matches the pattern
