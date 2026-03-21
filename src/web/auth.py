"""Authentication utilities for the Web UI."""

import os
from functools import wraps
from typing import Any, Callable

import aiohttp_session
import bcrypt
from aiohttp import web
from aiohttp_session import get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage


def setup_auth(app: web.Application, gateway_app: Any = None) -> None:
    """Setup session and authentication parameters for the app."""
    # Use a secure, random key for session storage if no environment key
    secret_key = os.getenv("WEB_SESSION_KEY")
    if secret_key:
        import hashlib

        fernet_key = hashlib.sha256(secret_key.encode("utf-8")).digest()
    else:
        # Check persistent db for a saved key
        if (
            gateway_app
            and gateway_app.web_config
            and "session_secret_key" in gateway_app.web_config
        ):
            import base64

            encoded_key = gateway_app.web_config["session_secret_key"]
            try:
                fernet_key = base64.b64decode(encoded_key.encode("utf-8"))
                if len(fernet_key) != 32:
                    raise ValueError("Key length invalid")
            except Exception:
                fernet_key = os.urandom(32)
                gateway_app.web_config["session_secret_key"] = base64.b64encode(
                    fernet_key
                ).decode("utf-8")
        else:
            fernet_key = os.urandom(32)
            if gateway_app and gateway_app.web_config is not None:
                import base64

                gateway_app.web_config["session_secret_key"] = base64.b64encode(
                    fernet_key
                ).decode("utf-8")

    aiohttp_session.setup(app, EncryptedCookieStorage(fernet_key))


def login_required(func: Callable) -> Callable:
    """Decorator to require login for a specific route."""

    @wraps(func)
    async def wrapper(request: web.Request, *args: Any, **kwargs: Any) -> Any:
        session = await get_session(request)
        if not session.get("logged_in"):
            raise web.HTTPFound("/login")
        return await func(request, *args, **kwargs)

    return wrapper


def verify_password(password: str, hashed: bytes) -> bool:
    """Verify a given password against a hashed one."""
    try:
        return bool(bcrypt.checkpw(password.encode("utf-8"), hashed))
    except Exception:
        return False


async def generate_csrf(request: web.Request) -> str:
    """Generate or retrieve a CSRF token for the current session."""
    import secrets

    session = await get_session(request)
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


async def validate_csrf(request: web.Request, form_data: dict = None) -> bool:
    """Validate a CSRF token from a form submission or header."""
    import secrets

    session = await get_session(request)
    expected = session.get("csrf_token")
    token = ""

    if form_data and "csrf_token" in form_data:
        token = form_data["csrf_token"]
    elif "X-CSRF-Token" in request.headers:
        token = request.headers["X-CSRF-Token"]

    if not expected or not token or not secrets.compare_digest(expected, token):
        return False
    return True
