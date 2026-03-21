"""Tests for web authentication utilities."""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import web

from src.web.auth import login_required, setup_auth


def test_setup_auth_with_env_key():
    """Test setup_auth uses WEB_SESSION_KEY if provided."""
    app = web.Application()
    with patch.dict(os.environ, {"WEB_SESSION_KEY": "my_test_key_1234"}):
        with patch("src.web.auth.aiohttp_session.setup") as mock_setup:
            setup_auth(app)

            mock_setup.assert_called_once()
            # The second argument to setup should be an EncryptedCookieStorage
            storage_arg = mock_setup.call_args[0][1]
            from aiohttp_session.cookie_storage import EncryptedCookieStorage

            assert isinstance(storage_arg, EncryptedCookieStorage)


def test_setup_auth_with_persistent_key():
    """Test setup_auth uses key from gateway_app.web_config."""
    app = web.Application()
    gateway_app = MagicMock()
    # A valid 32-byte fernet key, base64 encoded
    valid_key = base64.b64encode(os.urandom(32)).decode("utf-8")
    gateway_app.web_config = {"session_secret_key": valid_key}

    with patch.dict(os.environ, clear=True):
        with patch("src.web.auth.aiohttp_session.setup") as mock_setup:
            setup_auth(app, gateway_app)
            mock_setup.assert_called_once()


def test_setup_auth_creates_new_key_if_invalid():
    """Test setup_auth generates a new key if the existing one is invalid."""
    app = web.Application()
    gateway_app = MagicMock()
    # Invalid key (not 32 bytes)
    invalid_key = base64.b64encode(b"short").decode("utf-8")
    gateway_app.web_config = {"session_secret_key": invalid_key}

    with patch.dict(os.environ, clear=True):
        with patch("src.web.auth.aiohttp_session.setup"):
            setup_auth(app, gateway_app)
            # Should have generated a new key
            assert gateway_app.web_config["session_secret_key"] != invalid_key


def test_setup_auth_creates_new_key_if_none():
    """Test setup_auth generates a new key if none exists."""
    app = web.Application()
    gateway_app = MagicMock()
    gateway_app.web_config = {}

    with patch.dict(os.environ, clear=True):
        with patch("src.web.auth.aiohttp_session.setup"):
            setup_auth(app, gateway_app)
            assert "session_secret_key" in gateway_app.web_config


@pytest.mark.asyncio
async def test_login_required_decorator_logged_in():
    """Test login_required decorator passes if user is logged in."""

    # Create a dummy handler
    @login_required
    async def dummy_handler(request):
        return web.Response(text="Success")

    request = MagicMock()
    # Mock get_session to return a session dict with logged_in=True
    with patch("src.web.auth.get_session") as mock_get_session:
        mock_session = {"logged_in": True}
        mock_get_session.return_value = mock_session

        response = await dummy_handler(request)
        assert response.text == "Success"


@pytest.mark.asyncio
async def test_login_required_decorator_not_logged_in():
    """Test login_required decorator redirects if user is not logged in."""

    @login_required
    async def dummy_handler(request):
        return web.Response(text="Success")

    request = MagicMock()
    # Mock get_session to return empty session
    with patch("src.web.auth.get_session") as mock_get_session:
        mock_session = {}
        mock_get_session.return_value = mock_session

        with pytest.raises(web.HTTPFound) as exc_info:
            await dummy_handler(request)

        assert exc_info.value.location == "/login"


def test_verify_password():
    """Test verify_password properly checks hashes."""
    import bcrypt

    from src.web.auth import verify_password

    password = "my_secret_password"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    assert verify_password(password, b"invalid_hash") is False


@pytest.mark.asyncio
async def test_generate_and_validate_csrf():
    """Test generating and successfully validating a CSRF token."""
    from src.web.auth import generate_csrf, validate_csrf

    request = MagicMock()
    request.headers = {}

    mock_session = {}
    with patch("src.web.auth.get_session", return_value=mock_session):
        token = await generate_csrf(request)
        assert token is not None
        assert "csrf_token" in mock_session

        # Valid form token
        assert await validate_csrf(request, {"csrf_token": token}) is True

        # Invalid form token
        assert await validate_csrf(request, {"csrf_token": "wrong"}) is False

        # Valid header token
        request.headers = {"X-CSRF-Token": token}
        assert await validate_csrf(request, {}) is True
