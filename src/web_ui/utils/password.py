"""
Password utilities for simple authentication.
"""

import bcrypt
import sys
from typing import Optional


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        password_hash: Bcrypt hashed password

    Returns:
        bool: True if password matches hash, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_password_hash(password: Optional[str] = None) -> str:
    """
    Generate a password hash for CLI usage.

    Args:
        password: Password to hash (if None, will prompt for input)

    Returns:
        str: Bcrypt hashed password
    """
    if password is None:
        import getpass
        password = getpass.getpass("Enter password to hash: ")

    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    hashed = hash_password(password)
    print(f"Password hash: {hashed}")
    return hashed


def main():
    """CLI entry point for password hashing."""
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = None

    generate_password_hash(password)


if __name__ == "__main__":
    main()
