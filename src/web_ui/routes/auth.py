"""
Authentication routes for OAuth 2.0 integration.
"""

import logging
from flask import Blueprint, redirect, request, session, url_for, render_template, jsonify, current_app
from authlib.integrations.flask_client import OAuth

from ..services.oauth_client import OAuthClient
from ..models.user import UserManager

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

# Initialize OAuth client
oauth_client = OAuthClient()


@auth_bp.route("/login")
def login():
    """
    Initiate OAuth authentication flow.

    Supports multiple providers: google, apple, facebook, microsoft, yahoo
    """
    provider = request.args.get("provider", "google")

    try:
        # Get authorization URL
        auth_url = oauth_client.get_authorization_url(provider)

        if auth_url:
            return redirect(auth_url)
        else:
            return jsonify({"error": f"Unsupported OAuth provider: {provider}"}), 400

    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/callback")
def callback():
    """
    Handle OAuth callback and token exchange.
    """
    try:
        # Get authorization code from callback
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        if error:
            logger.warning(f"OAuth error: {error}")
            return render_template("login.html", error=f"Authentication failed: {error}")

        if not code:
            return render_template("login.html", error="No authorization code received")

        # Exchange code for token
        token_data = oauth_client.exchange_code_for_token(code, state)

        if not token_data:
            return render_template("login.html", error="Failed to exchange authorization code")

        # Get user information
        user_info = oauth_client.get_user_info(token_data)

        if not user_info:
            return render_template("login.html", error="Failed to retrieve user information")

        # Store user session
        user_manager = UserManager()
        user_manager.create_session(user_info, token_data)

        logger.info(f"User authenticated: {user_info.get('email', 'unknown')}")

        # Redirect to maps page
        return redirect(url_for("maps.index"))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return render_template("login.html", error="Authentication failed")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Terminate user session.
    """
    try:
        user_manager = UserManager()
        user_manager.destroy_session()

        logger.info("User logged out")

        return jsonify({"status": "success", "message": "Logged out successfully"})

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/status")
def status():
    """
    Check current authentication status.
    """
    try:
        user_manager = UserManager()
        user_info = user_manager.get_current_user()

        if user_info:
            return jsonify({
                "authenticated": True,
                "user": {
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "provider": user_info.get("provider")
                }
            })
        else:
            return jsonify({"authenticated": False})

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": "Status check failed"}), 500


@auth_bp.route("/user")
def user():
    """
    Get current user information.
    """
    try:
        user_manager = UserManager()
        user_info = user_manager.get_current_user()

        if user_info:
            return jsonify({
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "provider": user_info.get("provider"),
                "picture": user_info.get("picture")
            })
        else:
            return jsonify({"error": "Not authenticated"}), 401

    except Exception as e:
        logger.error(f"User info error: {e}")
        return jsonify({"error": "Failed to retrieve user information"}), 500
