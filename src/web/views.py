"""View handlers for the Web UI."""

import os
from typing import Any, Dict

import aiohttp_jinja2
import bcrypt
from aiohttp import web
from aiohttp_session import get_session

from .auth import login_required, verify_password


async def index(request: web.Request) -> web.Response:
    """Handle the root path, redirecting to dashboard if logged in."""
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/status")
    else:
        raise web.HTTPFound("/login")


@aiohttp_jinja2.template("login.html")  # type: ignore
async def login_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the login page."""
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/status")
    return {"error": ""}


@aiohttp_jinja2.template("login.html")  # type: ignore
async def login_post(request: web.Request) -> Dict[str, Any]:
    """Handle POST requests for the login page."""
    data = await request.post()
    password_val = data.get("password", "")
    # Handle case where value could be a string or a FileField. Expect string.
    password = str(password_val)

    # Simple single-user auth: look for admin password in ENV or db
    gateway_app = request.app["gateway_app"]

    # 1. Environment variable check
    env_password = os.getenv("WEB_ADMIN_PASSWORD")
    if env_password and password == env_password:
        session = await get_session(request)
        session["logged_in"] = True
        raise web.HTTPFound("/status")

    # 2. SQLite secure database check (admin_password hash)
    # We will use the config db for storing the web admin password hash
    db = gateway_app.web_config
    if "admin_password_hash" in db:
        hashed = db["admin_password_hash"].encode("utf-8")
        if verify_password(password, hashed):
            session = await get_session(request)
            session["logged_in"] = True
            raise web.HTTPFound("/status")

    # 3. Check for default admin password from config file
    config_password = gateway_app.config.web.admin_password
    if config_password and password == config_password:
        session = await get_session(request)
        session["logged_in"] = True
        raise web.HTTPFound("/status")

    return {"error": "Invalid password"}


async def logout(request: web.Request) -> web.Response:
    """Handle logout requests."""
    session = await get_session(request)
    session.pop("logged_in", None)
    raise web.HTTPFound("/login")


@login_required
@aiohttp_jinja2.template("config.html")  # type: ignore
async def config_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the config dashboard."""
    gateway_app = request.app["gateway_app"]
    db = gateway_app.web_config

    config_data = {
        "team_id": db.get("team_id", ""),
        "caltopo_connect_key_set": bool(
            db.get("caltopo_connect_key", gateway_app.config.caltopo.connect_key)
        ),
        "caltopo_group": db.get(
            "caltopo_group", gateway_app.config.caltopo.group or ""
        ),
        "allow_unknown_devices": db.get(
            "allow_unknown_devices", gateway_app.config.devices.allow_unknown_devices
        ),
        "nodes": db.get("nodes", gateway_app.config.nodes),
        "multiple_groups": db.get("multiple_groups", []),
        "success": request.query.get("success") == "1",
    }

    return config_data


@login_required
async def config_post(request: web.Request) -> web.Response:
    """Handle POST requests to update the configuration."""
    gateway_app = request.app["gateway_app"]
    db = gateway_app.web_config

    data = await request.post()

    # Update single settings
    db["team_id"] = str(data.get("team_id", "")).strip()

    # Only update connect key if one is provided (prevent empty overwrite)
    connect_key = str(data.get("caltopo_connect_key", "")).strip()
    if connect_key:
        db["caltopo_connect_key"] = connect_key

    db["caltopo_group"] = str(data.get("caltopo_group", "")).strip()

    # Checkbox logic (presence = true)
    db["allow_unknown_devices"] = data.get("allow_unknown_devices") == "on"

    # Node mappings array
    node_ids = data.getall("node_id[]", [])
    device_ids = data.getall("node_device_id[]", [])
    node_groups = data.getall("node_group[]", [])

    nodes_dict = {}
    for i in range(len(node_ids)):
        nid = str(node_ids[i]).strip()
        did = str(device_ids[i]).strip() if i < len(device_ids) else ""
        ngrp = str(node_groups[i]).strip() if i < len(node_groups) else ""
        if nid and did:
            nodes_dict[nid] = {"device_id": did, "group": ngrp if ngrp else None}

    db["nodes"] = nodes_dict

    # If an admin password is provided, hash and save it
    new_password = str(data.get("admin_password", "")).strip()
    if new_password:
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(new_password.encode("utf-8"), salt)
        db["admin_password_hash"] = hashed_bytes.decode("utf-8")

    # Update the multiple groups json.

    # Schedule an internal restart to apply the new configurations smoothly
    gateway_app = request.app["gateway_app"]
    gateway_app.restart_requested = True

    async def delayed_config_restart() -> None:
        import asyncio

        await asyncio.sleep(1.0)
        if gateway_app.stop_event:
            gateway_app.stop_event.set()

    import asyncio

    asyncio.create_task(delayed_config_restart())

    # Direct user back to config page, they will temporarily get connection refused
    # or login until app boots up fully
    raise web.HTTPFound("/config?success=1")


@login_required
async def restart_post(request: web.Request) -> web.Response:
    """Handle POST requests to trigger an internal application restart."""
    gateway_app = request.app["gateway_app"]
    gateway_app.restart_requested = True

    # Give the web response time to finish before setting the stop event
    async def delayed_stop() -> None:
        import asyncio

        await asyncio.sleep(1.0)
        if gateway_app.stop_event:
            gateway_app.stop_event.set()

    import asyncio

    asyncio.create_task(delayed_stop())

    return web.json_response({"status": "success", "message": "Restarting..."})


@login_required
async def api_logs_get(request: web.Request) -> web.Response:
    """Handle GET requests for just the system logs."""
    import collections

    gateway_app = request.app["gateway_app"]
    log_content = "No logs available."

    log_path = gateway_app.config.logging.file.path
    if log_path:
        try:
            import os

            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    deque = collections.deque(f, 100)
                    log_content = "".join(deque)
        except Exception as e:
            log_content = f"Error reading logs: {e}"

    # Return as plain text
    return web.Response(text=log_content, content_type="text/plain")


@login_required
@aiohttp_jinja2.template("status.html")  # type: ignore
async def status_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the status dashboard."""
    import collections

    gateway_app = request.app["gateway_app"]

    # Read last 100 lines of log
    log_lines = []
    log_path = gateway_app.config.logging.file.path
    if log_path and os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                deque = collections.deque(f, 100)
                log_lines = list(deque)
        except Exception:
            pass  # nosec B110

    return {
        "stats": gateway_app.stats,
        "device_states": gateway_app.device_states,
        "logs": "".join(log_lines),
    }
