"""
Tests for Flask application functionality.
"""

import unittest
import sys
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_ui import create_app


class TestFlaskApp(unittest.TestCase):
    """Test Flask application functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test configuration
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

        self.test_config_path = temp_file.name

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.test_config_path)
        except OSError:
            pass

    def test_app_creation(self):
        """Test Flask app creation."""
        app = create_app(self.test_config_path)

        self.assertIsNotNone(app)
        self.assertEqual(app.config['MESHTOPO_CONFIG'].caltopo.group, "TEST-GROUP")

    def test_blueprint_registration(self):
        """Test that all blueprints are registered."""
        app = create_app(self.test_config_path)

        # Check that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        self.assertIn('auth', blueprint_names)
        self.assertIn('maps', blueprint_names)
        self.assertIn('api', blueprint_names)
        self.assertIn('users', blueprint_names)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            response = client.get('/health')

            self.assertEqual(response.status_code, 200)
            self.assertIn('healthy', response.get_json()['status'])

    def test_root_redirect(self):
        """Test root endpoint redirects to maps."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            response = client.get('/')

            # Should redirect to maps page
            self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()
