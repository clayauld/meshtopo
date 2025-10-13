#!/usr/bin/env python3
"""
Test runner for Meshtopo Gateway Service.

This script runs all tests in the tests directory.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_tests():
    """Run all tests."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = str(PROJECT_ROOT)
    suite = loader.discover(
        start_dir, pattern="test_*.py", top_level_dir=str(PROJECT_ROOT)
    )

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
