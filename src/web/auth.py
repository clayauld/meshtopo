import base64
import os
from functools import wraps
from aiohttp import web
from aiohttp_session import get_session
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import bcrypt
from cryptography import fernet


def setup_auth(app: web.Application) -> None:
    # Use a secure, random key for session storage if not provided in environment
    secret_key = os.getenv("WEB_SESSION_KEY")
    if secret_key:
        fernet_key = secret_key.encode().ljust(32, b"0")[:32]
    else:
        fernet_key = os.urandom(32)

    aiohttp_session.setup(app, EncryptedCookieStorage(fernet_key))


def login_required(func):
    """Decorator to require login for a specific route."""

    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        session = await get_session(request)
        if not session.get("logged_in"):
            raise web.HTTPFound("/login")
        return await func(request, *args, **kwargs)

    return wrapper


def verify_password(password: str, hashed: bytes) -> bool:
    """Verify a given password against a hashed one."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception:
        return False
