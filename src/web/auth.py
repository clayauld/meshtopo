"""Authentication utilities for the Web UI."""

import os
from functools import wraps
from typing import Any, Callable

import aiohttp_session
import bcrypt
from aiohttp import web
from aiohttp_session import get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage


def setup_auth(app: web.Application) -> None:
    """Setup session and authentication parameters for the app."""
    # Use a secure, random key for session storage if no environment key
    secret_key = os.getenv("WEB_SESSION_KEY")
    if secret_key:
        fernet_key = secret_key.encode().ljust(32, b"0")[:32]
    else:
        fernet_key = os.urandom(32)

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
