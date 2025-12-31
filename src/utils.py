"""
Utility Functions

Common helpers used across the application, primarily for security
and data hygiene.
"""

import re
from typing import Any


def sanitize_for_log(input_str: Any) -> str:
    """
    Sanitize a string for safe logging.

    This function removes or escapes control characters (like newlines)
    to prevent **Log Injection** attacks (CWE-117). This ensures that
    an attacker cannot forge log entries by injecting newline characters
    into user-controlled input (like MQTT payloads or usernames).

    Args:
        input_str: The input string (or object convertible to string).

    Returns:
        A sanitized string safe for logging.
    """
    if input_str is None:
        return "None"

    s = str(input_str)
    # Replace newlines and carriage returns with escaped versions
    s = s.replace("\n", "\\n").replace("\r", "\\r")

    # Optional: Filter out other non-printable characters if strictly needed
    # For now, just ensuring single-line output is the primary defense.

    return s
