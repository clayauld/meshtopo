"""
User management routes for admin interface.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, session, flash

from ..utils.password import hash_password, verify_password
from ..models.user import UserManager
from ..models.config import ConfigManager

logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__)


def require_admin():
    """Require admin authentication."""
    user_manager = UserManager()
    if not user_manager.is_authenticated():
        flash("Please log in to access this page", "error")
        return redirect(url_for("auth.login"))

    if not user_manager.is_admin():
        flash("Admin access required", "error")
        return redirect(url_for("maps.index"))

    return None


@users_bp.route("/")
def index():
    """
    Display user management interface (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()

        users = config.get('users', [])

        return render_template(
            "users.html",
            users=users,
            current_user=UserManager().get_current_user()
        )

    except Exception as e:
        logger.error(f"Error loading users page: {e}")
        flash("Failed to load users page", "error")
        return render_template("users.html", users=[], current_user=None)


@users_bp.route("/add", methods=["POST"])
def add_user():
    """
    Add a new user (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user").strip()

        if not username or not password:
            flash("Username and password are required", "error")
            return redirect(url_for("users.index"))

        if role not in ["admin", "user"]:
            role = "user"

        # Check if user already exists
        config_manager = ConfigManager()
        config = config_manager.get_config()
        users = config.get('users', [])

        if any(user.get('username') == username for user in users):
            flash(f"User '{username}' already exists", "error")
            return redirect(url_for("users.index"))

        # Generate password hash
        password_hash = hash_password(password)

        # Create new user
        new_user = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "caltopo_credentials": None
        }

        # Add CalTopo credentials if provided
        credential_id = request.form.get("credential_id", "").strip()
        secret_key = request.form.get("secret_key", "").strip()

        if credential_id and secret_key:
            accessible_maps_input = request.form.get("accessible_maps", "").strip()
            accessible_maps = [m.strip() for m in accessible_maps_input.split(',') if m.strip()]

            new_user["caltopo_credentials"] = {
                "credential_id": credential_id,
                "secret_key": secret_key,
                "accessible_maps": accessible_maps
            }

        # Add user to config
        users.append(new_user)
        config['users'] = users

        # Save config
        config_manager.save_config(config)

        flash(f"User '{username}' added successfully", "success")
        logger.info(f"Admin added new user: {username}")

        return redirect(url_for("users.index"))

    except Exception as e:
        logger.error(f"Error adding user: {e}")
        flash("Failed to add user", "error")
        return redirect(url_for("users.index"))


@users_bp.route("/remove/<username>", methods=["POST"])
def remove_user(username):
    """
    Remove a user (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        users = config.get('users', [])

        # Find and remove user
        original_count = len(users)
        users = [user for user in users if user.get('username') != username]

        if len(users) == original_count:
            flash(f"User '{username}' not found", "error")
            return redirect(url_for("users.index"))

        # Save updated config
        config['users'] = users
        config_manager.save_config(config)

        flash(f"User '{username}' removed successfully", "success")
        logger.info(f"Admin removed user: {username}")

        return redirect(url_for("users.index"))

    except Exception as e:
        logger.error(f"Error removing user: {e}")
        flash("Failed to remove user", "error")
        return redirect(url_for("users.index"))


@users_bp.route("/update/<username>", methods=["POST"])
def update_user(username):
    """
    Update user information (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        users = config.get('users', [])

        # Find user
        user_index = None
        for i, user in enumerate(users):
            if user.get('username') == username:
                user_index = i
                break

        if user_index is None:
            flash(f"User '{username}' not found", "error")
            return redirect(url_for("users.index"))

        user = users[user_index]

        # Update role
        new_role = request.form.get("role", "").strip()
        if new_role in ["admin", "user"]:
            user["role"] = new_role

        # Update password if provided
        new_password = request.form.get("password", "").strip()
        if new_password:
            user["password_hash"] = hash_password(new_password)

        # Update CalTopo credentials
        credential_id = request.form.get("credential_id", "").strip()
        secret_key = request.form.get("secret_key", "").strip()

        if credential_id and secret_key:
            accessible_maps_input = request.form.get("accessible_maps", "").strip()
            accessible_maps = [m.strip() for m in accessible_maps_input.split(',') if m.strip()]

            user["caltopo_credentials"] = {
                "credential_id": credential_id,
                "secret_key": secret_key,
                "accessible_maps": accessible_maps
            }
        elif not credential_id and not secret_key:
            # Clear credentials if both are empty
            user["caltopo_credentials"] = None

        # Save updated config
        config_manager.save_config(config)

        flash(f"User '{username}' updated successfully", "success")
        logger.info(f"Admin updated user: {username}")

        return redirect(url_for("users.index"))

    except Exception as e:
        logger.error(f"Error updating user: {e}")
        flash("Failed to update user", "error")
        return redirect(url_for("users.index"))


@users_bp.route("/generate-hash", methods=["POST"])
def generate_hash():
    """
    Generate password hash for manual use (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        password = request.form.get("password", "").strip()

        if not password:
            flash("Password is required", "error")
            return redirect(url_for("users.index"))

        password_hash = hash_password(password)

        flash(f"Password hash generated: {password_hash}", "info")

        return redirect(url_for("users.index"))

    except Exception as e:
        logger.error(f"Error generating password hash: {e}")
        flash("Failed to generate password hash", "error")
        return redirect(url_for("users.index"))


@users_bp.route("/api/list")
def api_list_users():
    """
    API endpoint to list users (admin only).
    """
    auth_check = require_admin()
    if auth_check:
        return jsonify({"error": "Authentication required"}), 401

    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        users = config.get('users', [])

        # Remove sensitive information for API response
        safe_users = []
        for user in users:
            safe_user = {
                "username": user.get("username"),
                "role": user.get("role"),
                "has_caltopo_credentials": user.get("caltopo_credentials") is not None
            }
            safe_users.append(safe_user)

        return jsonify({"users": safe_users})

    except Exception as e:
        logger.error(f"Error listing users via API: {e}")
        return jsonify({"error": "Failed to list users"}), 500
