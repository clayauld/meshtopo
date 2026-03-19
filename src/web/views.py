import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session
import bcrypt
import os

from .auth import login_required, verify_password


async def index(request: web.Request) -> web.Response:
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/config")
    else:
        raise web.HTTPFound("/login")


@aiohttp_jinja2.template("login.html")
async def login_get(request: web.Request) -> dict:
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/config")
    return {"error": ""}


@aiohttp_jinja2.template("login.html")
async def login_post(request: web.Request) -> dict:
    data = await request.post()
    password = data.get("password", "")

    # Simple single-user auth: look for admin password in ENV or db
    gateway_app = request.app["gateway_app"]

    # 1. Environment variable check
    env_password = os.getenv("WEB_ADMIN_PASSWORD")
    if env_password and password == env_password:
        session = await get_session(request)
        session["logged_in"] = True
        raise web.HTTPFound("/config")

    # 2. SQLite secure database check (admin_password hash)
    # We will use the config db for storing the web admin password hash
    db = gateway_app.web_config
    if "admin_password_hash" in db:
        hashed = db["admin_password_hash"].encode("utf-8")
        if verify_password(password, hashed):
            session = await get_session(request)
            session["logged_in"] = True
            raise web.HTTPFound("/config")
    # 3. Check for default admin password from config file ONLY if no hash is set
    else:
        config_password = gateway_app.config.web.admin_password
        if config_password and __import__('hmac').compare_digest(password, config_password):
            session = await get_session(request)
            session["logged_in"] = True
            # Hash the default password on first successful login for future use
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db["admin_password_hash"] = hashed
            raise web.HTTPFound("/config")

    return {"error": "Invalid password"}


async def logout(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.pop("logged_in", None)
    raise web.HTTPFound("/login")


@login_required
@aiohttp_jinja2.template("config.html")
async def config_get(request: web.Request) -> dict:
    gateway_app = request.app["gateway_app"]
    db = gateway_app.web_config

    config_data = {
        "team_id": db.get("team_id", ""),
        "caltopo_connect_key_set": bool(db.get("caltopo_connect_key")),
        "caltopo_group": db.get("caltopo_group", ""),
        "multiple_groups": db.get("multiple_groups", []),
        "success": request.query.get("success") == "1",
    }

    return config_data


@login_required
async def config_post(request: web.Request) -> web.Response:
    gateway_app = request.app["gateway_app"]
    db = gateway_app.web_config

    data = await request.post()

    # Update single settings
    db["team_id"] = data.get("team_id", "").strip()

    # Only update connect key if one is provided (so we don't overwrite with empty string if they leave it blank)
    connect_key = data.get("caltopo_connect_key", "").strip()
    if connect_key:
        db["caltopo_connect_key"] = connect_key

    db["caltopo_group"] = data.get("caltopo_group", "").strip()

    # If an admin password is provided, hash and save it
    new_password = data.get("admin_password", "").strip()
    if new_password:
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        db["admin_password_hash"] = hashed

    # Update the multiple groups json. We expect dynamic form fields like multiple_groups[0][name]
    # For simplicity, we can parse multiple_groups as a list of dicts.

    raise web.HTTPFound("/config?success=1")
