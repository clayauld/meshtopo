"""
Utility functions for the Meshtopo gateway service.
"""

from typing import Any


def sanitize_for_log(text: Any) -> str:
    """
    Sanitize text for logging to prevent log injection.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized string with non-printable characters escaped
    """
    if text is None:
        return "None"

    # Convert to string and replace non-printable characters
    s = str(text)
    return "".join(c if c.isprintable() else f"\\x{ord(c):02x}" for c in s)
