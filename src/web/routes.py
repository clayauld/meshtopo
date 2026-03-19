"""Route definitions for the Web UI."""

from aiohttp import web

from .views import (
    config_get,
    config_post,
    index,
    login_get,
    login_post,
    logout,
)


def setup_routes(app: web.Application) -> None:
    """Register all routes for the web application."""
    app.router.add_get("/", index, name="index")
    app.router.add_get("/login", login_get, name="login")
    app.router.add_post("/login", login_post)
    app.router.add_get("/logout", logout, name="logout")
    app.router.add_get("/config", config_get, name="config")
    app.router.add_post("/config", config_post)
