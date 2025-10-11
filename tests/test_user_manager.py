"""
Tests for user session management.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_ui.models.user import UserManager
from config.config import UserConfig, UserCalTopoCredentials


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


if __name__ == '__main__':
    unittest.main()
