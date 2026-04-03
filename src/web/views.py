"""View handlers for the Web UI."""

import asyncio
import collections
import logging
import os
from typing import Any, Dict

import aiohttp_jinja2
import bcrypt
from aiohttp import web
from aiohttp_session import get_session

from .auth import generate_csrf, login_required, validate_csrf, verify_password
from .keys import GATEWAY_APP_KEY


async def get_common_context(request: web.Request, **kwargs: Any) -> Dict[str, Any]:
    """Helper to build common template context for all pages."""
    session = await get_session(request)
    gateway_app = request.app[GATEWAY_APP_KEY]

    context = {
        "username": session.get("username", "Guest"),
        "role": session.get("role", "guest"),
        "multi_tenant": gateway_app.config.web.multi_tenant_enabled,
        "csrf_token": await generate_csrf(request),
        "request_path": request.path,
        "success": request.query.get("success") == "1",
        "error": request.query.get("error"),
    }
    context.update(kwargs)
    return context


async def index(request: web.Request) -> web.Response:
    """Handle the root path, redirecting to dashboard if logged in."""
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/status")
    else:
        raise web.HTTPFound("/login")


@aiohttp_jinja2.template("login.html")
async def login_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the login page."""
    session = await get_session(request)
    if session.get("logged_in"):
        raise web.HTTPFound("/status")

    return await get_common_context(request)


@aiohttp_jinja2.template("login.html")
async def login_post(request: web.Request) -> Dict[str, Any]:
    """Handle POST requests for the login page."""
    data = await request.post()
    if not await validate_csrf(request, data):
        return {
            "error": "Invalid CSRF token.",
            "csrf_token": await generate_csrf(request),
        }

    password_val = data.get("password", "")
    password = str(password_val)
    username_val = data.get("username", "")
    username = str(username_val).strip()

    # Simple single-user auth: look for admin password in ENV or db
    gateway_app = request.app[GATEWAY_APP_KEY]
    multi_tenant = gateway_app.config.web.multi_tenant_enabled

    # 1. Environment variable check
    env_password = os.getenv("WEB_ADMIN_PASSWORD")
    db = gateway_app.web_config

    is_super_user = False

    if env_password and password == env_password:
        is_super_user = True
    if not is_super_user and "admin_password_hash" in db:
        hashed = db["admin_password_hash"].encode("utf-8")
        if verify_password(password, hashed):
            is_super_user = True
    if not is_super_user:
        config_password = gateway_app.config.web.admin_password
        if config_password and password == config_password:
            is_super_user = True

    if multi_tenant:
        if username == "admin" and is_super_user:
            session = await get_session(request)
            session["logged_in"] = True
            session["username"] = "admin"
            session["role"] = "super_user"
            raise web.HTTPFound("/status")
        elif username and username in gateway_app.tenants_db:
            tenant = gateway_app.tenants_db[username]
            if "password_hash" in tenant:
                if verify_password(password, tenant["password_hash"].encode("utf-8")):
                    session = await get_session(request)
                    session["logged_in"] = True
                    session["username"] = username
                    session["role"] = "tenant"
                    raise web.HTTPFound("/status")
        return {
            "error": "Invalid credentials",
            "csrf_token": await generate_csrf(request),
            "multi_tenant": True,
        }
    else:
        if is_super_user:
            session = await get_session(request)
            session["logged_in"] = True
            session["username"] = "admin"
            session["role"] = "super_user"
            raise web.HTTPFound("/status")

    return await get_common_context(request, error="Invalid password")


async def logout(request: web.Request) -> web.Response:
    """Handle logout requests."""
    session = await get_session(request)
    session.pop("logged_in", None)
    raise web.HTTPFound("/login")


@login_required
@aiohttp_jinja2.template("config.html")
async def config_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the config dashboard."""
    gateway_app = request.app[GATEWAY_APP_KEY]
    session = await get_session(request)
    role = session.get("role", "super_user")
    username = session.get("username", "admin")
    multi_tenant = gateway_app.config.web.multi_tenant_enabled

    if multi_tenant and role == "super_user":
        tenants = {
            k: {"caltopo_group": v.get("caltopo_group")}
            for k, v in list(gateway_app.tenants_db.items())
            if isinstance(v, dict)
        }

        # Aggregate all mapped nodes across all tenants
        mapped_nodes = []
        mapped_hw_ids = set()
        for t_user, t_data in list(gateway_app.tenants_db.items()):
            if not isinstance(t_data, dict):
                continue
            nodes = t_data.get("nodes", {})
            for hw_id, node_cfg in nodes.items():
                mapped_nodes.append(
                    {
                        "hardware_id": hw_id,
                        "tenant": t_user,
                        "device_id": node_cfg.get("device_id"),
                        "group": node_cfg.get("group"),
                    }
                )
                mapped_hw_ids.add(hw_id)
                # handle ! prefix
                if hw_id.startswith("!"):
                    mapped_hw_ids.add(hw_id[1:])
                else:
                    mapped_hw_ids.add(f"!{hw_id}")

        # Find unmapped devices (seen in device_states but not in mapped_hw_ids)
        unmapped_devices = []
        for hw_id, state in gateway_app.device_states.items():
            if hw_id not in mapped_hw_ids:
                unmapped_devices.append(
                    {
                        "hardware_id": hw_id,
                        "name": state.get("longname")
                        or state.get("shortname")
                        or "Unknown",
                    }
                )

        return await get_common_context(
            request,
            super_user=True,
            multi_tenant=True,
            tenants=tenants,
            mapped_nodes=mapped_nodes,
            unmapped_devices=unmapped_devices,
            unknown_devices_all_tenants=gateway_app.web_config.get(
                "unknown_devices_all_tenants",
                gateway_app.config.devices.unknown_devices_all_tenants,
            ),
        )

    # Fetch configuration for single tenant OR tenant-role
    if role == "tenant":
        db = gateway_app.tenants_db.get(username, {})
        config_data = await get_common_context(
            request,
            role="tenant",
            caltopo_connect_key_set=bool(db.get("caltopo_connect_key")),
            caltopo_group=db.get("caltopo_group", ""),
            nodes=db.get("nodes", {}),
        )
    else:
        db = gateway_app.web_config
        config_data = await get_common_context(
            request,
            role="super_user",
            team_id=db.get("team_id", ""),
            caltopo_connect_key_set=bool(
                db.get("caltopo_connect_key", gateway_app.config.caltopo.connect_key)
            ),
            caltopo_group=db.get(
                "caltopo_group", gateway_app.config.caltopo.group or ""
            ),
            allow_unknown_devices=db.get(
                "allow_unknown_devices",
                gateway_app.config.devices.allow_unknown_devices,
            ),
            nodes=db.get("nodes", gateway_app.config.nodes),
            multiple_groups=db.get("multiple_groups", []),
        )

    return config_data


@login_required
async def config_post(request: web.Request) -> web.Response:
    """Handle POST requests to update the configuration."""
    gateway_app = request.app[GATEWAY_APP_KEY]
    session = await get_session(request)
    role = session.get("role", "super_user")
    username = session.get("username", "admin")

    data = await request.post()
    if not await validate_csrf(request, data):
        raise web.HTTPForbidden(text="Invalid CSRF token")

    if role == "tenant":
        # Save tenant config
        if username not in gateway_app.tenants_db:
            gateway_app.tenants_db[username] = {}
        tenant_db = gateway_app.tenants_db[username]

        connect_key = str(data.get("caltopo_connect_key", "")).strip()
        if connect_key:
            tenant_db["caltopo_connect_key"] = connect_key

        tenant_db["caltopo_group"] = str(data.get("caltopo_group", "")).strip()

        # Update specific tenant's nodes
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
        tenant_db["nodes"] = nodes_dict

        # Save changes explicitly if persistentdict requires it
        gateway_app.tenants_db[username] = tenant_db
    else:
        action = str(data.get("action", ""))
        if gateway_app.config.web.multi_tenant_enabled:
            if action == "create_tenant":
                new_username = str(data.get("new_tenant_username", "")).strip()
                new_password = str(data.get("new_tenant_password", "")).strip()
                if new_username and new_password:
                    salt = bcrypt.gensalt()
                    hashed_bytes = bcrypt.hashpw(new_password.encode("utf-8"), salt)
                    gateway_app.tenants_db[new_username] = {
                        "password_hash": hashed_bytes.decode("utf-8"),
                        "nodes": {},
                        "caltopo_group": "",
                        "caltopo_connect_key": "",
                    }
                    raise web.HTTPFound("/config?success=1")
            elif action == "delete_tenant":
                admin_password = str(
                    data.get("delete_tenant_admin_password", "")
                ).strip()
                target_tenant = str(data.get("target_tenant", "")).strip()

                # Security check: verify admin password
                is_valid = False
                admin_hash = gateway_app.web_config.get("admin_password_hash")
                if admin_hash:
                    if verify_password(admin_password, admin_hash.encode("utf-8")):
                        is_valid = True
                if not is_valid:
                    if admin_password == gateway_app.config.web.admin_password:
                        is_valid = True

                if (
                    is_valid
                    and target_tenant
                    and target_tenant in gateway_app.tenants_db
                ):
                    del gateway_app.tenants_db[target_tenant]
                    raise web.HTTPFound("/config?success=1")
                else:
                    raise web.HTTPFound("/config?error=invalid_admin_password")
            elif action == "save_global":
                gateway_app.web_config["unknown_devices_all_tenants"] = (
                    data.get("unknown_devices_all_tenants") == "on"
                )
                raise web.HTTPFound("/config?success=1")
            elif action.startswith("assign_unmapped:"):
                # Superuser assigning an unmapped device
                idx = action.split(":")[1]
                hw_id = str(data.get(f"unmapped_hw_id_{idx}", ""))
                target_tenant = str(data.get(f"unmapped_tenant_{idx}", ""))
                device_id = str(data.get(f"unmapped_device_id_{idx}", ""))
                group = str(data.get(f"unmapped_group_{idx}", ""))

                if hw_id and target_tenant and target_tenant in gateway_app.tenants_db:
                    tenant_data = gateway_app.tenants_db[target_tenant]
                    if "nodes" not in tenant_data:
                        tenant_data["nodes"] = {}
                    tenant_data["nodes"][hw_id] = {
                        "device_id": device_id,
                        "group": group if group else None,
                    }
                    gateway_app.tenants_db[target_tenant] = tenant_data
                    raise web.HTTPFound("/config?success=1")
            # Individual remap/delete actions are now superseded by batch save.
            # We skip them here.

        db = gateway_app.web_config

        # Update single settings
        db["team_id"] = str(data.get("team_id", "")).strip()

        # Only update connect key if one is provided (prevent empty overwrite)
        connect_key = str(data.get("caltopo_connect_key", "")).strip()
        if connect_key:
            db["caltopo_connect_key"] = connect_key

        db["caltopo_group"] = str(data.get("caltopo_group", "")).strip()

        # Checkbox logic
        db["allow_unknown_devices"] = data.get("allow_unknown_devices") == "on"

        # Node mappings array
        if role == "super_user" and gateway_app.config.web.multi_tenant_enabled:
            # Batch update all nodes across all tenants
            hw_ids = data.getall("mapped_hw_id[]", [])
            target_tenants = data.getall("mapped_tenant[]", [])
            device_ids = data.getall("mapped_device_id[]", [])
            node_groups = data.getall("mapped_group[]", [])

            # Group by tenant
            tenant_updates: Dict[str, Dict[str, Any]] = {}
            for i in range(len(hw_ids)):
                hw_id = str(hw_ids[i]).strip()
                t_name = (
                    str(target_tenants[i]).strip() if i < len(target_tenants) else ""
                )
                did = str(device_ids[i]).strip() if i < len(device_ids) else ""
                ngrp = str(node_groups[i]).strip() if i < len(node_groups) else ""

                if hw_id and t_name and t_name in gateway_app.tenants_db:
                    if t_name not in tenant_updates:
                        tenant_updates[t_name] = {}
                    tenant_updates[t_name][hw_id] = {
                        "device_id": did,
                        "group": ngrp if ngrp else None,
                    }

            # Apply updates: Clear and reload nodes for each affected tenant
            # (Note: This currently only updates tenants present in the form.
            # To be 100% thorough, we should clear nodes for ALL tenants
            # because some might have had all their nodes deleted.)
            # Apply updates only for tenants that were present in the form
            managed_tenants = data.getall("managed_tenant_name[]", [])
            for t_val in managed_tenants:
                t_name = str(t_val)
                if t_name in gateway_app.tenants_db:
                    tenant_data = gateway_app.tenants_db[t_name]
                    if not isinstance(tenant_data, dict):
                        continue
                    tenant_data["nodes"] = tenant_updates.get(t_name, {})
                    gateway_app.tenants_db[t_name] = tenant_data
        else:
            # Standard single-tenant or legacy update
            node_ids = data.getall("node_id[]", [])
            device_ids = data.getall("node_device_id[]", [])
            node_groups = data.getall("node_group[]", [])

            nodes_dict = {}
            for i in range(len(node_ids)):
                nid = str(node_ids[i]).strip()
                did = str(device_ids[i]).strip() if i < len(device_ids) else ""
                ngrp = str(node_groups[i]).strip() if i < len(node_groups) else ""
                if nid and did:
                    nodes_dict[nid] = {
                        "device_id": did,
                        "group": ngrp if ngrp else None,
                    }

            db["nodes"] = nodes_dict

        # If an admin password is provided, hash and save it
        new_password = str(data.get("admin_password", "")).strip()
        if new_password:
            salt = bcrypt.gensalt()
            hashed_bytes = bcrypt.hashpw(new_password.encode("utf-8"), salt)
            db["admin_password_hash"] = hashed_bytes.decode("utf-8")

    # Update the multiple groups json.

    # Schedule an internal restart to apply the new configurations smoothly
    gateway_app = request.app[GATEWAY_APP_KEY]
    gateway_app.restart_requested = True

    async def delayed_config_restart() -> None:

        await asyncio.sleep(1.0)
        if gateway_app.stop_event:
            gateway_app.stop_event.set()

    asyncio.create_task(delayed_config_restart())

    # Direct user back to config page, they will temporarily get connection refused
    # or login until app boots up fully
    raise web.HTTPFound("/config?success=1")


@login_required
async def restart_post(request: web.Request) -> web.Response:
    """Handle POST requests to trigger an internal application restart."""
    if not await validate_csrf(request):
        raise web.HTTPForbidden(text="Invalid CSRF token")

    gateway_app = request.app[GATEWAY_APP_KEY]
    gateway_app.restart_requested = True

    # Give the web response time to finish before setting the stop event
    async def delayed_stop() -> None:

        await asyncio.sleep(1.0)
        if gateway_app.stop_event:
            gateway_app.stop_event.set()

    asyncio.create_task(delayed_stop())

    return web.json_response({"status": "success", "message": "Restarting..."})


@login_required
async def api_logs_get(request: web.Request) -> web.Response:
    """Handle GET requests for just the system logs."""

    gateway_app = request.app[GATEWAY_APP_KEY]
    log_content = "No logs available."

    log_path = gateway_app.config.logging.file.path
    if log_path:
        try:
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    deque = collections.deque(f, 100)
                    log_content = "".join(deque)
        except Exception:
            logging.exception("Error reading logs from %s", log_path)
            log_content = "Error reading logs."

    # Return as plain text
    return web.Response(text=log_content, content_type="text/plain")


@login_required
@aiohttp_jinja2.template("status.html")
async def status_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the status dashboard."""

    gateway_app = request.app[GATEWAY_APP_KEY]

    # Read last 100 lines of log
    log_lines = []
    log_path = gateway_app.config.logging.file.path
    if log_path and os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                deque = collections.deque(f, 100)
                log_lines = list(deque)
        except Exception:
            logging.exception("Error reading logs for status page from %s", log_path)

    # Inject configured names and tenant names if available
    display_states = {}
    for hw_id, state in gateway_app.device_states.items():
        display_state = dict(state)
        callsign = None
        tenant_name = None

        # Check multi-tenant configured nodes first
        if gateway_app.config.web.multi_tenant_enabled and gateway_app.tenants_db:
            for t_user, t_data in list(gateway_app.tenants_db.items()):
                if isinstance(t_data, dict):
                    nodes = t_data.get("nodes", {})
                    if hw_id in nodes:
                        callsign = nodes[hw_id].get("device_id")
                        tenant_name = t_user
                    elif hw_id.startswith("!") and hw_id[1:] in nodes:
                        callsign = nodes[hw_id[1:]].get("device_id")
                        tenant_name = t_user
                    elif not hw_id.startswith("!") and f"!{hw_id}" in nodes:
                        callsign = nodes[f"!{hw_id}"].get("device_id")
                        tenant_name = t_user
                    if callsign:
                        break

        # Check single-tenant global config
        if not callsign and hasattr(gateway_app, "_get_or_create_callsign"):
            if not gateway_app.config.web.multi_tenant_enabled:
                callsign = gateway_app._get_or_create_callsign(hw_id)

        display_state["configured_name"] = callsign
        display_state["tenant_name"] = tenant_name
        display_states[hw_id] = display_state

    session = await get_session(request)
    role = session.get("role", "super_user")
    username = session.get("username", "admin")

    # Filter for tenants
    final_display_states = {}
    stats_to_display = dict(gateway_app.stats)

    if role == "tenant":
        # Calculate isolated tenant stats
        tenant_stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "position_updates_sent": 0,
            "errors": 0,
            "start_time": gateway_app.stats.get("start_time", 0.0),
        }
        for hw_id, state in display_states.items():
            if state.get("tenant_name") == username:
                final_display_states[hw_id] = state
                # Aggregate per-device stats
                tenant_stats["messages_processed"] += state.get("messages_processed", 0)
                tenant_stats["position_updates_sent"] += state.get(
                    "position_updates_sent", 0
                )

        # Approximate messages_received as processed for the tenant view
        tenant_stats["messages_received"] = tenant_stats["messages_processed"]
        stats_to_display = tenant_stats
    else:
        final_display_states = display_states

    return {
        "stats": stats_to_display,
        "device_states": final_display_states,
        "logs": "".join(log_lines),
        "multi_tenant": gateway_app.config.web.multi_tenant_enabled,
        "role": role,
        "username": username,
        "csrf_token": await generate_csrf(request),
    }


@login_required
@aiohttp_jinja2.template("admin.html")
async def admin_panel_get(request: web.Request) -> Dict[str, Any]:
    """Handle GET requests for the admin panel (super-user only)."""
    session = await get_session(request)
    if session.get("role") != "super_user":
        raise web.HTTPForbidden(text="Admin access required")

    gateway_app = request.app[GATEWAY_APP_KEY]
    return await get_common_context(
        request, 
        title="User Management",
        tenants=gateway_app.tenants_db
    )


@login_required
async def admin_panel_post(request: web.Request) -> web.Response:
    """Handle POST requests for tenant management in the admin panel."""
    # Ensure super-user
    session = await get_session(request)
    if session.get("role") != "super_user":
        raise web.HTTPForbidden(text="Admin access required")

    data = await request.post()
    if not await validate_csrf(request, data):
        raise web.HTTPForbidden(text="Invalid CSRF token")

    gateway_app = request.app[GATEWAY_APP_KEY]
    
    # 1. New Tenant Creation
    new_username = str(data.get("new_username", "")).strip()
    new_password = str(data.get("new_password", "")).strip()
    if new_username and new_password:
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(new_password.encode("utf-8"), salt)
        gateway_app.tenants_db[new_username] = {
            "password_hash": hashed_bytes.decode("utf-8"),
            "caltopo_connect_key": str(data.get("new_caltopo_key", "")).strip(),
            "caltopo_group": str(data.get("new_caltopo_group", "")).strip(),
            "nodes": {}
        }
        raise web.HTTPFound("/admin?success=1")

    # 2. Tenant Deletion
    delete_username = str(data.get("delete_username", "")).strip()
    if delete_username and delete_username in gateway_app.tenants_db:
        del gateway_app.tenants_db[delete_username]
        raise web.HTTPFound("/admin?success=1")

    raise web.HTTPFound("/admin")
