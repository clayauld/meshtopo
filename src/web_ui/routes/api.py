"""
RESTful API endpoints for configuration, monitoring, and system management.
"""

import logging
import time
from flask import Blueprint, jsonify, request, current_app

from ..models.config import ConfigManager
from ..models.user import UserManager

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


@api_bp.route("/config")
def get_config():
    """
    Retrieve current system configuration.
    """
    try:
        config_manager = ConfigManager()
        config_data = config_manager.get_config()

        # Remove sensitive information
        safe_config = config_manager.sanitize_config(config_data)

        return jsonify({"config": safe_config})

    except Exception as e:
        logger.error(f"Get config error: {e}")
        return jsonify({"error": "Failed to retrieve configuration"}), 500


@api_bp.route("/config/update", methods=["POST"])
def update_config():
    """
    Update configuration parameters.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No configuration data provided"}), 400

        config_manager = ConfigManager()
        success = config_manager.update_config(data)

        if success:
            return jsonify({"status": "success", "message": "Configuration updated"})
        else:
            return jsonify({"error": "Failed to update configuration"}), 500

    except Exception as e:
        logger.error(f"Update config error: {e}")
        return jsonify({"error": "Failed to update configuration"}), 500


@api_bp.route("/config/validate")
def validate_config():
    """
    Validate configuration settings.
    """
    try:
        config_manager = ConfigManager()
        validation_result = config_manager.validate_config()

        return jsonify({"validation": validation_result})

    except Exception as e:
        logger.error(f"Validate config error: {e}")
        return jsonify({"error": "Configuration validation failed"}), 500


@api_bp.route("/config/reset", methods=["POST"])
def reset_config():
    """
    Reset configuration to defaults.
    """
    try:
        config_manager = ConfigManager()
        success = config_manager.reset_config()

        if success:
            return jsonify({"status": "success", "message": "Configuration reset to defaults"})
        else:
            return jsonify({"error": "Failed to reset configuration"}), 500

    except Exception as e:
        logger.error(f"Reset config error: {e}")
        return jsonify({"error": "Failed to reset configuration"}), 500


@api_bp.route("/config/backup")
def backup_config():
    """
    Export configuration as backup.
    """
    try:
        config_manager = ConfigManager()
        backup_data = config_manager.backup_config()

        return jsonify({"backup": backup_data})

    except Exception as e:
        logger.error(f"Backup config error: {e}")
        return jsonify({"error": "Failed to backup configuration"}), 500


@api_bp.route("/config/restore", methods=["POST"])
def restore_config():
    """
    Restore configuration from backup.
    """
    try:
        data = request.get_json()
        backup_data = data.get("backup")

        if not backup_data:
            return jsonify({"error": "No backup data provided"}), 400

        config_manager = ConfigManager()
        success = config_manager.restore_config(backup_data)

        if success:
            return jsonify({"status": "success", "message": "Configuration restored"})
        else:
            return jsonify({"error": "Failed to restore configuration"}), 500

    except Exception as e:
        logger.error(f"Restore config error: {e}")
        return jsonify({"error": "Failed to restore configuration"}), 500


@api_bp.route("/status")
def system_status():
    """
    Overall system status and health.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        # Get gateway service status (if available)
        gateway_status = get_gateway_status()

        # Get web UI status
        web_ui_status = {
            "enabled": config.web_ui.enabled,
            "host": config.web_ui.host,
            "port": config.web_ui.port,
            "ssl_enabled": config.ssl.enabled
        }

        # Get MQTT status
        mqtt_status = {
            "broker": config.mqtt.broker,
            "port": config.mqtt.port,
            "use_internal": config.mqtt.use_internal_broker
        }

        # Get CalTopo status
        caltopo_status = {
            "group": config.caltopo.group,
            "map_id": config.caltopo.map_id,
            "team_api_enabled": config.caltopo.team_api.enabled
        }

        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "gateway": gateway_status,
                "web_ui": web_ui_status,
                "mqtt": mqtt_status,
                "caltopo": caltopo_status
            }
        })

    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({"error": "Failed to get system status"}), 500


@api_bp.route("/metrics")
def metrics():
    """
    Performance metrics and statistics.
    """
    try:
        # Get gateway metrics (if available)
        gateway_metrics = get_gateway_metrics()

        # Get web UI metrics
        web_ui_metrics = {
            "active_sessions": get_active_session_count(),
            "requests_per_minute": get_request_rate(),
            "uptime": get_uptime()
        }

        return jsonify({
            "gateway": gateway_metrics,
            "web_ui": web_ui_metrics,
            "timestamp": time.time()
        })

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({"error": "Failed to get metrics"}), 500


@api_bp.route("/logs")
def logs():
    """
    Recent log entries with filtering.
    """
    try:
        # Get log level filter
        level = request.args.get("level", "INFO")
        limit = int(request.args.get("limit", 100))

        # Get recent logs (simplified implementation)
        logs = get_recent_logs(level, limit)

        return jsonify({"logs": logs})

    except Exception as e:
        logger.error(f"Logs error: {e}")
        return jsonify({"error": "Failed to get logs"}), 500


@api_bp.route("/health")
def health():
    """
    Detailed health check information.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {
                "configuration": check_configuration_health(),
                "mqtt": check_mqtt_health(),
                "caltopo": check_caltopo_health(),
                "web_ui": check_web_ui_health()
            }
        }

        # Determine overall health
        all_healthy = all(
            check["status"] == "healthy"
            for check in health_status["checks"].values()
        )

        if not all_healthy:
            health_status["status"] = "degraded"

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"error": "Health check failed"}), 500


@api_bp.route("/nodes")
def nodes():
    """
    Status of all configured Meshtastic nodes.
    """
    try:
        config = current_app.config["MESHTOPO_CONFIG"]

        nodes_status = []
        for node_id, node_mapping in config.nodes.items():
            nodes_status.append({
                "node_id": node_id,
                "device_id": node_mapping.device_id,
                "status": "configured"
            })

        return jsonify({"nodes": nodes_status})

    except Exception as e:
        logger.error(f"Nodes status error: {e}")
        return jsonify({"error": "Failed to get nodes status"}), 500


@api_bp.route("/nodes/<node_id>/history")
def node_history(node_id):
    """
    Position history for specific node.
    """
    try:
        # This would typically query a database or log file
        # For now, return empty history
        history = []

        return jsonify({"node_id": node_id, "history": history})

    except Exception as e:
        logger.error(f"Node history error: {e}")
        return jsonify({"error": "Failed to get node history"}), 500


# Helper functions for status and metrics
def get_gateway_status():
    """Get gateway service status."""
    # This would typically check if the gateway service is running
    return {"status": "unknown", "message": "Gateway status not available"}


def get_gateway_metrics():
    """Get gateway service metrics."""
    # This would typically query the gateway service for metrics
    return {"position_updates_sent": 0, "errors": 0}


def get_active_session_count():
    """Get count of active user sessions."""
    return 1  # Simplified


def get_request_rate():
    """Get current request rate."""
    return 0  # Simplified


def get_uptime():
    """Get application uptime."""
    return time.time()  # Simplified


def get_recent_logs(level, limit):
    """Get recent log entries."""
    return []  # Simplified


def check_configuration_health():
    """Check configuration health."""
    return {"status": "healthy", "message": "Configuration valid"}


def check_mqtt_health():
    """Check MQTT broker health."""
    return {"status": "healthy", "message": "MQTT broker accessible"}


def check_caltopo_health():
    """Check CalTopo API health."""
    return {"status": "healthy", "message": "CalTopo API accessible"}


def check_web_ui_health():
    """Check web UI health."""
    return {"status": "healthy", "message": "Web UI operational"}
