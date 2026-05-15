# Module `utils`

Utility functions for the MeshTopo gateway service.

## Functions

## `def decode_psk(psk: str) -> bytes`

Robustly decode a Meshtastic Pre-Shared Key (PSK).
Handles Hex, Base64 (with or without padding), and URL-safe Base64.

Args:
    psk: The PSK string to decode.

Returns:
    The decoded key as bytes.

Raises:
    ValueError: If the key cannot be decoded.

## `def sanitize_for_log(text: Any) -> str`

Sanitize text for logging to prevent log injection.

Args:
    text: Text to sanitize

Returns:
    Sanitized string with non-printable characters escaped
