"""
Tests for password utilities.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_ui.utils.password import hash_password, verify_password


class TestPasswordUtilities(unittest.TestCase):
    """Test password hashing and verification utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Should return a string
        self.assertIsInstance(hashed, str)

        # Should be different from original password
        self.assertNotEqual(password, hashed)

        # Should start with bcrypt identifier
        self.assertTrue(hashed.startswith("$2b$"))

    def test_verify_password(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Correct password should verify
        self.assertTrue(verify_password(password, hashed))

        # Wrong password should not verify
        self.assertFalse(verify_password("wrong_password", hashed))

        # Empty password should not verify
        self.assertFalse(verify_password("", hashed))

    def test_password_consistency(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different salts should produce different hashes
        self.assertNotEqual(hash1, hash2)

        # But both should verify correctly
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))


if __name__ == '__main__':
    unittest.main()
