from aiohttp import web
import aiohttp_jinja2
import jinja2
import os

from .routes import setup_routes
from .auth import setup_auth


async def create_app(gateway_app):
    """Create and configure the aiohttp web application."""
    app = web.Application()

    # Attach gateway_app so handlers can access it
    app["gateway_app"] = gateway_app

    # Setup Jinja2 templates
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_dir))

    # Setup session and auth
    setup_auth(app)

    # Setup routes
    setup_routes(app)

    return app
