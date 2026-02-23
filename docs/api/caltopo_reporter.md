# Module `caltopo_reporter`

CalTopo API integration for sending position reports.

## Classes

## `class CalTopoReporter`

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

### `def __init__(self, config: Any, client: Optional[httpx.AsyncClient] = None) -> None`

Initialize CalTopo reporter.

Args:
    config: Configuration object containing CalTopo settings
    client: Optional shared httpx.AsyncClient. If not provided, a new client
           will be created for each request.

### `def _is_valid_caltopo_identifier(self, identifier: str) -> bool`

Validate that a CalTopo identifier (connect_key or group) is safe.

Args:
    identifier: The identifier to validate

Returns:
    bool: True if the identifier is valid, False otherwise

### `def _make_api_request(self, client: httpx.AsyncClient, url: str, callsign: str, endpoint_type: str) -> bool`

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

### `def _redact_secrets(self, text: str) -> str`

Redact sensitive information (connect_key/group) from text.

This method replaces any occurrence of a secret key in the CalTopo URL
path with '<REDACTED>'. It targets segments following the BASE_URL that
consist of valid identifier characters.

Args:
    text: The text to redact (e.g. log message, exception string)

Returns:
    str: The redacted text

### `def _send_to_connect_key(self, client: httpx.AsyncClient, callsign: str, latitude: float, longitude: float) -> bool`

Internal method to send position data to a personal connect_key endpoint.

### `def _send_to_group(self, client: httpx.AsyncClient, callsign: str, latitude: float, longitude: float, group: str) -> bool`

Internal method to send position data to a team 'group' endpoint.

### `def _test_connect_key_endpoint(self, client: httpx.AsyncClient) -> bool`

Test connection to connect_key endpoint.

### `def _test_group_endpoint(self, client: httpx.AsyncClient) -> bool`

Test connection to group endpoint.

### `def _validate_and_log_identifier(self, identifier: str, identifier_type: str) -> bool`

Validate a CalTopo identifier and log an error if invalid.

Args:
    identifier: The identifier to validate
    identifier_type: The type of identifier (e.g., 'connect_key', 'group')
                   for error logging

Returns:
    bool: True if the identifier is valid, False otherwise

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
    bool: True if at least one endpoint (connect_key or group) was
          successfully updated, False otherwise.

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
