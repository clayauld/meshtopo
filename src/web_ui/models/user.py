"""
User session management for simple authentication.
"""

import logging
from typing import Dict, Optional, Any
from flask import session

logger = logging.getLogger(__name__)


class UserManager:
    """User session management for simple authentication."""

    def __init__(self):
        """Initialize user manager."""
        self.session_key = "meshtopo_user"

    def create_session(self, user_config: Any) -> bool:
        """
        Create user session with user configuration.

        Args:
            user_config: User configuration from config

        Returns:
            bool: True if session created successfully
        """
        try:
            session_data = {
                "username": user_config.username,
                "role": user_config.role,
                "has_caltopo_credentials": user_config.caltopo_credentials is not None,
                "caltopo_credentials": {
                    "credential_id": user_config.caltopo_credentials.credential_id,
                    "secret_key": user_config.caltopo_credentials.secret_key,
                    "accessible_maps": user_config.caltopo_credentials.accessible_maps
                } if user_config.caltopo_credentials else None,
                "authenticated": True
            }

            session[self.session_key] = session_data
            session.permanent = True

            logger.info(f"Created session for user: {user_config.username}")
            return True

        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return False

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user information from session.

        Returns:
            dict: User information or None if not authenticated
        """
        try:
            session_data = session.get(self.session_key)

            if not session_data or not session_data.get("authenticated"):
                return None

            return session_data

        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    def get_caltopo_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Get current user's CalTopo credentials from session.

        Returns:
            dict: CalTopo credentials or None if not authenticated or no credentials
        """
        try:
            session_data = session.get(self.session_key)

            if not session_data or not session_data.get("authenticated"):
                return None

            return session_data.get("caltopo_credentials")

        except Exception as e:
            logger.error(f"Failed to get CalTopo credentials: {e}")
            return None

    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.

        Returns:
            bool: True if user is authenticated
        """
        try:
            session_data = session.get(self.session_key)
            return session_data and session_data.get("authenticated", False)

        except Exception as e:
            logger.error(f"Failed to check authentication status: {e}")
            return False

    def is_admin(self) -> bool:
        """
        Check if current user is an admin.

        Returns:
            bool: True if user is admin
        """
        try:
            session_data = session.get(self.session_key)
            return session_data and session_data.get("role") == "admin"

        except Exception as e:
            logger.error(f"Failed to check admin status: {e}")
            return False

    def destroy_session(self) -> bool:
        """
        Destroy current user session.

        Returns:
            bool: True if session destroyed successfully
        """
        try:
            if self.session_key in session:
                del session[self.session_key]

            logger.info("User session destroyed")
            return True

        except Exception as e:
            logger.error(f"Failed to destroy user session: {e}")
            return False

    def get_username(self) -> Optional[str]:
        """
        Get current user's username.

        Returns:
            str: Username or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("username") if user_info else None

    def get_role(self) -> Optional[str]:
        """
        Get current user's role.

        Returns:
            str: User role or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("role") if user_info else None

    def has_caltopo_access(self) -> bool:
        """
        Check if current user has CalTopo credentials.

        Returns:
            bool: True if user has CalTopo credentials
        """
        user_info = self.get_current_user()
        return user_info.get("has_caltopo_credentials", False) if user_info else False
