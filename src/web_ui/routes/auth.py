"""
Simple authentication routes for username/password login.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, session, flash

from ..utils.password import verify_password
from ..models.user import UserManager

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.

    GET: Display login form
    POST: Validate credentials and create session
    """
    if request.method == "GET":
        return render_template("login.html")

    # Handle POST request
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    remember_me = request.form.get("remember_me") == "on"

    if not username or not password:
        flash("Username and password are required", "error")
        return render_template("login.html")

    try:
        # Get configuration
        config = current_app.config["MESHTOPO_CONFIG"]

        # Find user in configuration
        user_config = config.get_user_by_username(username)
        if not user_config:
            flash("Invalid username or password", "error")
            return render_template("login.html")

        # Verify password
        if not verify_password(password, user_config.password_hash):
            flash("Invalid username or password", "error")
            return render_template("login.html")

        # Create user session
        user_manager = UserManager()
        success = user_manager.create_session(user_config)

        if success:
            logger.info(f"User logged in: {username}")

            # Set session timeout based on remember me
            if remember_me:
                session.permanent = True
            else:
                session.permanent = False

            # Redirect to maps page
            return redirect(url_for("maps.index"))
        else:
            flash("Failed to create session", "error")
            return render_template("login.html")

    except Exception as e:
        logger.error(f"Login error: {e}")
        flash("Login failed. Please try again.", "error")
        return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Terminate user session.
    """
    try:
        user_manager = UserManager()
        user_manager.destroy_session()

        logger.info("User logged out")
        flash("You have been logged out", "info")

        return redirect(url_for("auth.login"))

    except Exception as e:
        logger.error(f"Logout error: {e}")
        flash("Logout failed", "error")
        return redirect(url_for("auth.login"))


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
                    "username": user_info.get("username"),
                    "role": user_info.get("role")
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
                "username": user_info.get("username"),
                "role": user_info.get("role"),
                "has_caltopo_credentials": user_info.get("has_caltopo_credentials", False)
            })
        else:
            return jsonify({"error": "Not authenticated"}), 401

    except Exception as e:
        logger.error(f"User info error: {e}")
        return jsonify({"error": "Failed to retrieve user information"}), 500
