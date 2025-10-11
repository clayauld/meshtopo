"""
OAuth 2.0 client for multiple provider integration.
"""

import logging
import secrets
import time
from typing import Dict, Optional, Any
from urllib.parse import urlencode

import requests
from authlib.integrations.flask_client import OAuth

logger = logging.getLogger(__name__)


class OAuthClient:
    """OAuth 2.0 client supporting multiple providers."""

    def __init__(self):
        """Initialize OAuth client."""
        self.oauth = OAuth()
        self.providers = {
            "google": {
                "client_id": "",
                "client_secret": "",
                "authorize_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile"
            },
            "apple": {
                "client_id": "",
                "client_secret": "",
                "authorize_url": "https://appleid.apple.com/auth/authorize",
                "token_url": "https://appleid.apple.com/auth/token",
                "userinfo_url": "https://appleid.apple.com/auth/userinfo",
                "scope": "name email"
            },
            "facebook": {
                "client_id": "",
                "client_secret": "",
                "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
                "userinfo_url": "https://graph.facebook.com/me",
                "scope": "email"
            },
            "microsoft": {
                "client_id": "",
                "client_secret": "",
                "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "scope": "openid email profile"
            },
            "yahoo": {
                "client_id": "",
                "client_secret": "",
                "authorize_url": "https://api.login.yahoo.com/oauth2/request_auth",
                "token_url": "https://api.login.yahoo.com/oauth2/get_token",
                "userinfo_url": "https://api.login.yahoo.com/openid/v1/userinfo",
                "scope": "openid email profile"
            }
        }

    def configure_provider(self, provider: str, client_id: str, client_secret: str, redirect_uri: str):
        """
        Configure OAuth provider credentials.

        Args:
            provider: OAuth provider name
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
        """
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        self.providers[provider]["client_id"] = client_id
        self.providers[provider]["client_secret"] = client_secret
        self.providers[provider]["redirect_uri"] = redirect_uri

    def get_authorization_url(self, provider: str) -> Optional[str]:
        """
        Get OAuth authorization URL for the specified provider.

        Args:
            provider: OAuth provider name

        Returns:
            str: Authorization URL or None if provider not configured
        """
        if provider not in self.providers:
            logger.error(f"Unsupported OAuth provider: {provider}")
            return None

        provider_config = self.providers[provider]

        if not provider_config["client_id"]:
            logger.error(f"OAuth provider {provider} not configured")
            return None

        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        params = {
            "client_id": provider_config["client_id"],
            "redirect_uri": provider_config["redirect_uri"],
            "scope": provider_config["scope"],
            "response_type": "code",
            "state": state
        }

        auth_url = f"{provider_config['authorize_url']}?{urlencode(params)}"

        # Store state for validation
        self._store_state(state, provider)

        return auth_url

    def exchange_code_for_token(self, code: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter for CSRF protection

        Returns:
            dict: Token data or None if exchange failed
        """
        try:
            # Validate state
            provider = self._validate_state(state)
            if not provider:
                logger.error("Invalid OAuth state parameter")
                return None

            provider_config = self.providers[provider]

            # Exchange code for token
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": provider_config["client_id"],
                "client_secret": provider_config["client_secret"],
                "redirect_uri": provider_config["redirect_uri"]
            }

            response = requests.post(
                provider_config["token_url"],
                data=token_data,
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                token_info = response.json()
                token_info["provider"] = provider
                return token_info
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None

    def get_user_info(self, token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get user information using access token.

        Args:
            token_data: Token data from exchange_code_for_token

        Returns:
            dict: User information or None if failed
        """
        try:
            provider = token_data.get("provider")
            if not provider or provider not in self.providers:
                logger.error(f"Invalid provider in token data: {provider}")
                return None

            provider_config = self.providers[provider]
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error("No access token in token data")
                return None

            # Get user info
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(provider_config["userinfo_url"], headers=headers)

            if response.status_code == 200:
                user_info = response.json()
                user_info["provider"] = provider
                return user_info
            else:
                logger.error(f"User info request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"User info error: {e}")
            return None

    def _store_state(self, state: str, provider: str):
        """Store OAuth state for validation."""
        # In a production environment, this should be stored in a secure session store
        # For now, we'll use a simple in-memory store
        if not hasattr(self, "_state_store"):
            self._state_store = {}

        self._state_store[state] = {
            "provider": provider,
            "timestamp": time.time()
        }

    def _validate_state(self, state: str) -> Optional[str]:
        """Validate OAuth state parameter."""
        if not hasattr(self, "_state_store"):
            return None

        state_data = self._state_store.get(state)
        if not state_data:
            return None

        # Check if state is not too old (5 minutes)
        if time.time() - state_data["timestamp"] > 300:
            del self._state_store[state]
            return None

        # Clean up used state
        del self._state_store[state]

        return state_data["provider"]
