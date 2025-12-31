# Module `utils`

Utility Functions

Common helpers used across the application, primarily for security
and data hygiene.

## Functions

## `def sanitize_for_log(input_str: Any) -> str`

Sanitize a string for safe logging.

This function removes or escapes control characters (like newlines)
to prevent **Log Injection** attacks (CWE-117). This ensures that
an attacker cannot forge log entries by injecting newline characters
into user-controlled input (like MQTT payloads or usernames).

Args:
    input_str: The input string (or object convertible to string).

Returns:
    A sanitized string safe for logging.
