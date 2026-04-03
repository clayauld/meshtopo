"""Route definitions for the Web UI."""

from aiohttp import web

from .views import (
    admin_panel_get,
    admin_panel_post,
    api_logs_get,
    config_get,
    config_post,
    index,
    login_get,
    login_post,
    logout,
    restart_post,
    status_get,
)


def setup_routes(app: web.Application) -> None:
    """Register all routes for the web application."""
    app.router.add_get("/", index, name="index")
    app.router.add_get("/status", status_get, name="status")
    app.router.add_get("/login", login_get, name="login")
    app.router.add_post("/login", login_post)
    app.router.add_get("/logout", logout, name="logout")
    app.router.add_get("/admin", admin_panel_get, name="admin")
    app.router.add_post("/admin", admin_panel_post)
    app.router.add_post("/api/restart", restart_post)
    app.router.add_get("/api/logs", api_logs_get)
    app.router.add_get("/config", config_get, name="config")
    app.router.add_post("/config", config_post)
