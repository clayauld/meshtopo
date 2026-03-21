"""Web UI module for Gateway Configuration."""

import os
from typing import TYPE_CHECKING

import aiohttp_jinja2
import jinja2
from aiohttp import web

from .auth import setup_auth
from .routes import setup_routes

if TYPE_CHECKING:
    from gateway_app import GatewayApp


async def create_app(gateway_app: "GatewayApp") -> web.Application:
    """Create and configure the aiohttp web application.

    Args:
        gateway_app: The main gateway application instance.

    Returns:
        The configured aiohttp web application.
    """
    app = web.Application()

    # Attach gateway_app so handlers can access it
    app["gateway_app"] = gateway_app

    # Setup Jinja2 templates
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_dir))

    # Setup session and auth
    setup_auth(app, gateway_app)

    # Setup routes
    setup_routes(app)

    return app
