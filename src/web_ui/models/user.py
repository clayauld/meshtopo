"""
User session management for web UI authentication.
"""

import logging
from typing import Dict, Optional, Any
from flask import session

logger = logging.getLogger(__name__)


class UserManager:
    """User session management."""

    def __init__(self):
        """Initialize user manager."""
        self.session_key = "meshtopo_user"

    def create_session(self, user_info: Dict[str, Any], token_data: Dict[str, Any]) -> bool:
        """
        Create user session with user information and token data.

        Args:
            user_info: User information from OAuth provider
            token_data: OAuth token data

        Returns:
            bool: True if session created successfully
        """
        try:
            session_data = {
                "user_info": user_info,
                "token_data": token_data,
                "authenticated": True
            }

            session[self.session_key] = session_data
            session.permanent = True

            logger.info(f"Created session for user: {user_info.get('email', 'unknown')}")
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

            return session_data.get("user_info")

        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    def get_token_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current user's token data from session.

        Returns:
            dict: Token data or None if not authenticated
        """
        try:
            session_data = session.get(self.session_key)

            if not session_data or not session_data.get("authenticated"):
                return None

            return session_data.get("token_data")

        except Exception as e:
            logger.error(f"Failed to get token data: {e}")
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

    def update_user_info(self, user_info: Dict[str, Any]) -> bool:
        """
        Update user information in current session.

        Args:
            user_info: Updated user information

        Returns:
            bool: True if update successful
        """
        try:
            session_data = session.get(self.session_key)

            if not session_data or not session_data.get("authenticated"):
                logger.warning("No authenticated session to update")
                return False

            session_data["user_info"] = user_info
            session[self.session_key] = session_data

            logger.info("Updated user information in session")
            return True

        except Exception as e:
            logger.error(f"Failed to update user info: {e}")
            return False

    def get_user_email(self) -> Optional[str]:
        """
        Get current user's email address.

        Returns:
            str: User email or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("email") if user_info else None

    def get_user_name(self) -> Optional[str]:
        """
        Get current user's display name.

        Returns:
            str: User name or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("name") if user_info else None

    def get_user_provider(self) -> Optional[str]:
        """
        Get current user's OAuth provider.

        Returns:
            str: OAuth provider or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("provider") if user_info else None

    def get_user_picture(self) -> Optional[str]:
        """
        Get current user's profile picture URL.

        Returns:
            str: Profile picture URL or None if not authenticated
        """
        user_info = self.get_current_user()
        return user_info.get("picture") if user_info else None
