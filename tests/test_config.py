"""
Test configuration and utilities for the test suite.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_test_config():
    """Create a temporary test configuration file."""
    config_content = """
mqtt:
    broker: localhost
    port: 1883
    username: ''
    password: ''
    topic: "msh/REGION/2/json/+/+"

caltopo:
    connect_key: TEST_CONNECT_KEY

nodes:
    '!test123':
        device_id: TEST-DEVICE

logging:
    level: INFO
    file:
        enabled: true
        path: test.log
        max_size: 10MB
        backup_count: 5
"""

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(config_content)
    temp_file.close()

    return temp_file.name


def cleanup_test_config(config_path):
    """Clean up temporary test configuration file."""
    try:
        os.unlink(config_path)
    except OSError:
        pass


class TestCase(unittest.TestCase):
    """Base test case with common utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config_path = create_test_config()

    def tearDown(self):
        """Clean up test fixtures."""
        cleanup_test_config(self.test_config_path)
