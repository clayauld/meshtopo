"""
Map management routes for CalTopo integration.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app

from ..services.caltopo_api import CalTopoTeamAPI
from ..models.config import ConfigManager

logger = logging.getLogger(__name__)

maps_bp = Blueprint("maps", __name__)


@maps_bp.route("/")
def index():
    """
    Map selection interface.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        # Check if user is authenticated
        from ..models.user import UserManager
        user_manager = UserManager()
        user_info = user_manager.get_current_user()

        if not user_info:
            return redirect(url_for("auth.login"))

        # Get available maps if Team API is enabled
        maps = []
        if config.caltopo.team_api.enabled:
            caltopo_api = CalTopoTeamAPI(config)
            maps = caltopo_api.list_maps()

        # Get current map selection
        config_manager = ConfigManager()
        current_map = config_manager.get_current_map()

        return render_template(
            "maps.html",
            maps=maps,
            current_map=current_map,
            team_api_enabled=config.caltopo.team_api.enabled
        )

    except Exception as e:
        logger.error(f"Map index error: {e}")
        return render_template("maps.html", error="Failed to load maps")


@maps_bp.route("/list")
def list_maps():
    """
    Retrieve all available CalTopo maps.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        if not config.caltopo.team_api.enabled:
            return jsonify({"error": "CalTopo Team API not enabled"}), 400

        caltopo_api = CalTopoTeamAPI(config)
        maps = caltopo_api.list_maps()

        return jsonify({"maps": maps})

    except Exception as e:
        logger.error(f"List maps error: {e}")
        return jsonify({"error": "Failed to retrieve maps"}), 500


@maps_bp.route("/current")
def current_map():
    """
    Get currently selected map configuration.
    """
    try:
        config_manager = ConfigManager()
        current_map = config_manager.get_current_map()

        return jsonify({"map": current_map})

    except Exception as e:
        logger.error(f"Current map error: {e}")
        return jsonify({"error": "Failed to get current map"}), 500


@maps_bp.route("/select", methods=["POST"])
def select_map():
    """
    Select target map for position forwarding.
    """
    try:
        data = request.get_json()
        map_id = data.get("map_id")

        if not map_id:
            return jsonify({"error": "Map ID is required"}), 400

        config_manager = ConfigManager()
        success = config_manager.select_map(map_id)

        if success:
            logger.info(f"Map selected: {map_id}")
            return jsonify({"status": "success", "map_id": map_id})
        else:
            return jsonify({"error": "Failed to select map"}), 500

    except Exception as e:
        logger.error(f"Select map error: {e}")
        return jsonify({"error": "Failed to select map"}), 500


@maps_bp.route("/<map_id>")
def map_details(map_id):
    """
    Get detailed information about specific map.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        if not config.caltopo.team_api.enabled:
            return jsonify({"error": "CalTopo Team API not enabled"}), 400

        caltopo_api = CalTopoTeamAPI(config)
        map_info = caltopo_api.get_map_details(map_id)

        if map_info:
            return jsonify({"map": map_info})
        else:
            return jsonify({"error": "Map not found"}), 404

    except Exception as e:
        logger.error(f"Map details error: {e}")
        return jsonify({"error": "Failed to get map details"}), 500


@maps_bp.route("/<map_id>/status")
def map_status(map_id):
    """
    Get real-time status of map integration.
    """
    try:
        config_manager = ConfigManager()
        status = config_manager.get_map_status(map_id)

        return jsonify({"status": status})

    except Exception as e:
        logger.error(f"Map status error: {e}")
        return jsonify({"error": "Failed to get map status"}), 500


@maps_bp.route("/<map_id>/test", methods=["POST"])
def test_map(map_id):
    """
    Test connection to specific map.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        if not config.caltopo.team_api.enabled:
            return jsonify({"error": "CalTopo Team API not enabled"}), 400

        caltopo_api = CalTopoTeamAPI(config)
        success = caltopo_api.test_map_connection(map_id)

        if success:
            return jsonify({"status": "success", "message": "Map connection test passed"})
        else:
            return jsonify({"error": "Map connection test failed"}), 500

    except Exception as e:
        logger.error(f"Test map error: {e}")
        return jsonify({"error": "Map test failed"}), 500
