"""
Test configuration and utilities for the test suite.
"""

import unittest
import tempfile
import os
import sys
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
    topic: msh/2/json/+/+

caltopo:
    group: TEST-GROUP
    map_id: ''
    team_api:
        enabled: false
        credential_id: ''
        secret_key: ''

users:
    - username: admin
      password_hash: $2b$12$test_hash
      role: admin
      caltopo_credentials:
          credential_id: test_cred_id
          secret_key: test_secret_key
          accessible_maps: [map1]

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
    web_ui:
        level: INFO
        access_log: true

web_ui:
    host: 127.0.0.1
    port: 5000
    secret_key: test_secret_key
    session:
        timeout: 3600
        secure: false
        httponly: true
    rate_limit:
        enabled: false
        requests_per_minute: 60

ssl:
    enabled: false
    cert_file: ''
    key_file: ''
"""

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
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
