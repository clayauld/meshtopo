"""
Utility functions for the MeshTopo gateway service.
"""

import base64
import binascii
import hashlib
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


def decode_psk(psk: str) -> bytes:
    """
    Robustly decode a Meshtastic Pre-Shared Key (PSK).
    Handles Hex, Base64 (with or without padding), and URL-safe Base64.

    Args:
        psk: The PSK string to decode.

    Returns:
        The decoded key as bytes.

    Raises:
        ValueError: If the key cannot be decoded.
    """
    psk = psk.strip()
    if not psk:
        return b""

    # Explicit prefix for plaintext passwords
    if psk.startswith("pass:") or psk.startswith("text:"):
        passphrase = psk.split(":", 1)[1]
        return hashlib.sha256(passphrase.encode("utf-8")).digest()

    # 1. Try Hex (with 0x prefix)
    if psk.startswith("0x") or psk.startswith("0X"):
        try:
            return bytes.fromhex(psk[2:])
        except ValueError:
            pass

    # 2. Try Hex (without prefix)
    if len(psk) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in psk):
        try:
            return bytes.fromhex(psk)
        except ValueError:
            pass

    # 3. Try Base64
    # Fix missing padding
    padding = len(psk) % 4
    if padding > 0:
        psk += "=" * (4 - padding)

    try:
        # Convert URL-safe characters to standard Base64 characters
        std_psk = psk.replace("-", "+").replace("_", "/")
        decoded = base64.b64decode(std_psk)
        # Only return if it's a valid AES key size.
        # If not, it's likely a plaintext passphrase.
        if len(decoded) in (16, 24, 32):
            return decoded
    except binascii.Error:
        pass

    # 4. Fallback: Treat as plaintext passphrase
    # The Meshtastic app takes plaintext passwords and generates a 256-bit key
    # using the SHA256 hash of the string.
    return hashlib.sha256(psk.encode("utf-8")).digest()
