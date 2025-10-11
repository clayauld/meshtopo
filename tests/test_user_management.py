"""
Tests for user management functionality.
"""

import unittest
from tests.test_config import TestCase
from src.web_ui import create_app


class TestUserManagement(TestCase):
    """Test user management functionality."""

    def test_users_page_requires_admin(self):
        """Test that users page requires admin authentication."""
        app = create_app(self.test_config_path)

        with app.test_client() as client:
            # Test unauthenticated access
            response = client.get('/users/')
            self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_user(self):
        """Test adding a new user."""
        app = create_app(self.test_config_path)

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
        app = create_app(self.test_config_path)

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
    unittest.main()
