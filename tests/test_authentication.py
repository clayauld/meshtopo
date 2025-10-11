"""
Tests for authentication flow.
"""

import unittest
from tests.test_config import TestCase, create_test_config, cleanup_test_config
from src.web_ui import create_app
from src.web_ui.utils.password import hash_password


class TestAuthenticationFlow(TestCase):
    """Test complete authentication flow."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test configuration with hashed password
        test_password = "admin123"
        password_hash = hash_password(test_password)

        config_content = f"""
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
      password_hash: {password_hash}
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
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write(config_content)
        temp_file.close()

        self.test_config_path = temp_file.name

    def tearDown(self):
        """Clean up test fixtures."""
        cleanup_test_config(self.test_config_path)

    def test_login_success(self):
        """Test successful login."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            # Test login page
            response = client.get('/auth/login')
            self.assertEqual(response.status_code, 200)

            # Test successful login
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': self._get_csrf_token(client)
            })

            # Should redirect to maps page
            self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        """Test failed login."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            # Test failed login
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'wrong_password',
                'csrf_token': self._get_csrf_token(client)
            })

            # Should return login page with error
            self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """Test logout functionality."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            # Login first
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': self._get_csrf_token(client)
            })

            # Test logout
            response = client.post('/auth/logout', data={
                'csrf_token': self._get_csrf_token(client)
            })

            # Should redirect to login page
            self.assertEqual(response.status_code, 302)

    def test_auth_status(self):
        """Test authentication status endpoint."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            # Test unauthenticated status
            response = client.get('/auth/status')
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.get_json()['authenticated'])

            # Login
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': self._get_csrf_token(client)
            })

            # Test authenticated status
            response = client.get('/auth/status')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()['authenticated'])

    def _get_csrf_token(self, client):
        """Helper method to get CSRF token from login page."""
        response = client.get('/auth/login')
        # In a real implementation, you'd parse the HTML to extract the CSRF token
        # For testing purposes, we'll use a mock token
        return "test_csrf_token"


if __name__ == '__main__':
    unittest.main()
