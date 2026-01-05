# Module `utils`

Utility functions for the Meshtopo gateway service.

## Functions

## `def sanitize_for_log(text: Any) -> str`

Sanitize text for logging to prevent log injection.

Args:
    text: Text to sanitize

Returns:
    Sanitized string with non-printable characters escaped
