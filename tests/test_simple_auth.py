"""
Comprehensive test suite for the simplified authentication system.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_ui.utils.password import hash_password, verify_password
from src.web_ui.models.user import UserManager
from src.web_ui.routes.auth import auth_bp
from src.web_ui.routes.users import users_bp
from src.web_ui import create_app
from config.config import Config, UserConfig, UserCalTopoCredentials


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


class TestUserManager(unittest.TestCase):
    """Test user session management."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_manager = UserManager()

        # Create mock user config
        self.user_config = UserConfig(
            username="testuser",
            password_hash="$2b$12$test_hash",
            role="user",
            caltopo_credentials=UserCalTopoCredentials(
                credential_id="test_cred_id",
                secret_key="test_secret_key",
                accessible_maps=["map1", "map2"]
            )
        )

    def test_create_session(self):
        """Test session creation."""
        # Mock Flask session
        with patch('src.web_ui.models.user.session') as mock_session:
            result = self.user_manager.create_session(self.user_config)

            self.assertTrue(result)
            mock_session.__setitem__.assert_called()

    def test_get_current_user(self):
        """Test getting current user from session."""
        # Mock Flask session with user data
        mock_session_data = {
            'meshtopo_user': {
                'username': 'testuser',
                'role': 'user',
                'has_caltopo_credentials': True
            }
        }

        with patch('src.web_ui.models.user.session', mock_session_data):
            user_info = self.user_manager.get_current_user()

            self.assertIsNotNone(user_info)
            self.assertEqual(user_info['username'], 'testuser')
            self.assertEqual(user_info['role'], 'user')

    def test_is_authenticated(self):
        """Test authentication status check."""
        # Test authenticated user
        mock_session_data = {'meshtopo_user': {'username': 'testuser'}}
        with patch('src.web_ui.models.user.session', mock_session_data):
            self.assertTrue(self.user_manager.is_authenticated())

        # Test unauthenticated user
        with patch('src.web_ui.models.user.session', {}):
            self.assertFalse(self.user_manager.is_authenticated())

    def test_is_admin(self):
        """Test admin role check."""
        # Test admin user
        mock_session_data = {'meshtopo_user': {'role': 'admin'}}
        with patch('src.web_ui.models.user.session', mock_session_data):
            self.assertTrue(self.user_manager.is_admin())

        # Test regular user
        mock_session_data = {'meshtopo_user': {'role': 'user'}}
        with patch('src.web_ui.models.user.session', mock_session_data):
            self.assertFalse(self.user_manager.is_admin())

    def test_destroy_session(self):
        """Test session destruction."""
        with patch('src.web_ui.models.user.session') as mock_session:
            result = self.user_manager.destroy_session()

            self.assertTrue(result)
            mock_session.pop.assert_called_with('meshtopo_user', None)


class TestFlaskApp(unittest.TestCase):
    """Test Flask application functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # Create test configuration
        test_config = """
mqtt:
    broker: "localhost"
    port: 1883
    username: ""
    password: ""
    topic: "msh/REGION/2/json/+/+"

caltopo:
    group: "TEST-GROUP"
    map_id: ""
    team_api:
        enabled: false
        credential_id: ""
        secret_key: ""

users:
    - username: "admin"
      password_hash: "$2b$12$test_hash"
      role: "admin"
      caltopo_credentials:
          credential_id: "test_cred_id"
          secret_key: "test_secret_key"
          accessible_maps: ["map1"]

nodes:
    "!test123":
        device_id: "TEST-DEVICE"

logging:
    level: "INFO"
    file:
        enabled: true
        path: "test.log"
        max_size: "10MB"
        backup_count: 5
    web_ui:
        level: "INFO"
        access_log: true

web_ui:
    host: "127.0.0.1"
    port: 5000
    secret_key: "test_secret_key"
    session:
        timeout: 3600
        secure: false
        httponly: true
    rate_limit:
        enabled: true
        requests_per_minute: 60

ssl:
    enabled: false
    cert_file: ""
    key_file: ""
"""

        with open(self.config_path, 'w') as f:
            f.write(test_config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_app_creation(self):
        """Test Flask app creation."""
        app = create_app(self.config_path)

        self.assertIsNotNone(app)
        self.assertEqual(app.config['MESHTOPO_CONFIG'].caltopo.group, "TEST-GROUP")

    def test_blueprint_registration(self):
        """Test that all blueprints are registered."""
        app = create_app(self.config_path)

        # Check that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        self.assertIn('auth', blueprint_names)
        self.assertIn('maps', blueprint_names)
        self.assertIn('api', blueprint_names)
        self.assertIn('users', blueprint_names)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        app = create_app(self.config_path)

        with app.test_client() as client:
            response = client.get('/health')

            self.assertEqual(response.status_code, 200)
            self.assertIn('healthy', response.get_json()['status'])

    def test_root_redirect(self):
        """Test root endpoint redirects to maps."""
        app = create_app(self.config_path)

        with app.test_client() as client:
            response = client.get('/')

            # Should redirect to maps page
            self.assertEqual(response.status_code, 302)


class TestAuthenticationFlow(unittest.TestCase):
    """Test complete authentication flow."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # Create test configuration with hashed password
        test_password = "admin123"
        password_hash = hash_password(test_password)

        test_config = f"""
mqtt:
    broker: "localhost"
    port: 1883
    username: ""
    password: ""
    topic: "msh/REGION/2/json/+/+"

caltopo:
    group: "TEST-GROUP"
    map_id: ""
    team_api:
        enabled: false
        credential_id: ""
        secret_key: ""

users:
    - username: "admin"
      password_hash: "{password_hash}"
      role: "admin"
      caltopo_credentials:
          credential_id: "test_cred_id"
          secret_key: "test_secret_key"
          accessible_maps: ["map1"]

nodes:
    "!test123":
        device_id: "TEST-DEVICE"

logging:
    level: "INFO"
    file:
        enabled: true
        path: "test.log"
        max_size: "10MB"
        backup_count: 5
    web_ui:
        level: "INFO"
        access_log: true

web_ui:
    host: "127.0.0.1"
    port: 5000
    secret_key: "test_secret_key"
    session:
        timeout: 3600
        secure: false
        httponly: true
    rate_limit:
        enabled: false
        requests_per_minute: 60

ssl:
    enabled: false
    cert_file: ""
    key_file: ""
"""

        with open(self.config_path, 'w') as f:
            f.write(test_config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_login_success(self):
        """Test successful login."""
        app = create_app(self.config_path)

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
        app = create_app(self.config_path)

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
        app = create_app(self.config_path)

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
        app = create_app(self.config_path)

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


class TestUserManagement(unittest.TestCase):
    """Test user management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

        # Create test configuration
        test_config = """
mqtt:
    broker: "localhost"
    port: 1883
    username: ""
    password: ""
    topic: "msh/REGION/2/json/+/+"

caltopo:
    group: "TEST-GROUP"
    map_id: ""
    team_api:
        enabled: false
        credential_id: ""
        secret_key: ""

users:
    - username: "admin"
      password_hash: "$2b$12$test_hash"
      role: "admin"
      caltopo_credentials:
          credential_id: "test_cred_id"
          secret_key: "test_secret_key"
          accessible_maps: ["map1"]

nodes:
    "!test123":
        device_id: "TEST-DEVICE"

logging:
    level: "INFO"
    file:
        enabled: true
        path: "test.log"
        max_size: "10MB"
        backup_count: 5
    web_ui:
        level: "INFO"
        access_log: true

web_ui:
    host: "127.0.0.1"
    port: 5000
    secret_key: "test_secret_key"
    session:
        timeout: 3600
        secure: false
        httponly: true
    rate_limit:
        enabled: false
        requests_per_minute: 60

ssl:
    enabled: false
    cert_file: ""
    key_file: ""
"""

        with open(self.config_path, 'w') as f:
            f.write(test_config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_users_page_requires_admin(self):
        """Test that users page requires admin authentication."""
        app = create_app(self.config_path)

        with app.test_client() as client:
            # Test unauthenticated access
            response = client.get('/users/')
            self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_user(self):
        """Test adding a new user."""
        app = create_app(self.config_path)

        with app.test_client() as client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': 'test_csrf_token'
            })

            # Add new user
            response = client.post('/users/add', data={
                'username': 'newuser',
                'password': 'newpass123',
                'role': 'user',
                'csrf_token': 'test_csrf_token'
            })

            # Should redirect back to users page
            self.assertEqual(response.status_code, 302)

    def test_remove_user(self):
        """Test removing a user."""
        app = create_app(self.config_path)

        with app.test_client() as client:
            # Login as admin
            client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': 'test_csrf_token'
            })

            # Remove user
            response = client.post('/users/remove/testuser', data={
                'csrf_token': 'test_csrf_token'
            })

            # Should redirect back to users page
            self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
