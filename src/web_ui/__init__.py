"""
Flask application factory for the Meshtopo web UI.
"""

import logging
import os
import secrets
from pathlib import Path

from flask import Flask
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from config.config import Config


def create_app(config_path: str = "config/config.yaml") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_path: Path to the configuration file

    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    try:
        config = Config.from_file(config_path)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise

    # Configure Flask app
    app.config.update(
        SECRET_KEY=config.web_ui.secret_key or secrets.token_hex(32),
        SESSION_TYPE="filesystem",
        SESSION_FILE_DIR="/tmp/flask_session",
        SESSION_PERMANENT=False,
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX="meshtopo:",
        SESSION_COOKIE_SECURE=config.web_ui.session.secure,
        SESSION_COOKIE_HTTPONLY=config.web_ui.session.httponly,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=config.web_ui.session.timeout,
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=None,
    )

    # Configure logging
    if config.logging.web_ui.level:
        app.logger.setLevel(getattr(logging, config.logging.web_ui.level.upper()))

    # Initialize extensions
    Session(app)
    CSRFProtect(app)

    # Configure rate limiting
    if config.web_ui.rate_limit.enabled:
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[f"{config.web_ui.rate_limit.requests_per_minute} per minute"],
        )

        # Add specific rate limits for authentication endpoints
        limiter.limit("5 per minute")(app.route("/auth/login", methods=["POST"]))
        limiter.limit("10 per minute")(app.route("/auth/logout", methods=["POST"]))

    else:
        limiter = None

    # Store configuration and limiter in app context
    app.config["MESHTOPO_CONFIG"] = config
    app.config["LIMITER"] = limiter

    # Add user context processor
    @app.context_processor
    def inject_user():
        """Inject user information into template context."""
        from .models.user import UserManager
        user_manager = UserManager()
        user_info = user_manager.get_current_user()
        return dict(user_info=user_info)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.maps import maps_bp
    from .routes.api import api_bp
    from .routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(maps_bp, url_prefix="/maps")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/users")

    # Add health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint for load balancers."""
        return {"status": "healthy", "service": "meshtopo-web-ui"}, 200

    # Add root redirect to maps page
    @app.route("/")
    def index():
        """Redirect to maps page."""
        from flask import redirect, url_for
        return redirect(url_for("maps.index"))

    return app
