#!/usr/bin/env python3
"""
Test script for the Meshtopo gateway service.
"""

import logging
import sys
import unittest
from pathlib import Path

# Add parent directory and src directory to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Local imports after path modification
from config.config import Config  # noqa: E402
from gateway_app import GatewayApp  # noqa: E402


def test_config_loading() -> bool:
    """Test configuration loading."""
    print("Testing configuration loading...")

    try:
        # Test with example config
        config = Config.from_file(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        print("✓ Configuration loaded successfully")

        # Test node mapping
        device_id = config.get_node_device_id("!823a4edc")
        assert device_id == "TEAM-LEAD", f"Expected 'TEAM-LEAD', got '{device_id}'"
        print("✓ Node mapping works correctly")

        # Test unmapped node
        device_id = config.get_node_device_id("!unknown")
        assert device_id is None, f"Expected None, got '{device_id}'"
        print("✓ Unmapped node handling works correctly")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_message_processing() -> bool:
    """Test message processing logic."""
    print("\nTesting message processing...")

    try:
        # Create a test configuration
        config = Config.from_file(str(PROJECT_ROOT / "config" / "config.yaml.example"))

        # Create gateway app
        app = GatewayApp(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        app.config = config

        # Initialize CalTopo reporter
        from caltopo_reporter import CalTopoReporter

        app.caltopo_reporter = CalTopoReporter(config)

        # Test position message with correct field names
        test_message = {
            "from": 862485920,  # Numeric node ID
            "sender": "!823a4edc",  # Hardware ID
            "type": "position",
            "payload": {"latitude_i": 612188460, "longitude_i": -1499001320},
        }

        # Process the message
        app._process_message(test_message)

        print("✓ Message processing completed")
        print(f"  Messages received: {app.stats['messages_received']}")
        print(f"  Messages processed: {app.stats['messages_processed']}")
        print(f"  Position updates sent: {app.stats['position_updates_sent']}")
        print(f"  Errors: {app.stats['errors']}")

        return True

    except Exception as e:
        print(f"✗ Message processing test failed: {e}")
        return False


def test_caltopo_url_building() -> bool:
    """Test CalTopo URL building."""
    print("\nTesting CalTopo URL building...")

    try:
        config = Config.from_file(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        from caltopo_reporter import CalTopoReporter

        reporter = CalTopoReporter(config)

        # Test URL building
        url = reporter._build_api_url("TEST-DEVICE", 61.218846, -149.900132)
        expected = (
            "https://caltopo.com/api/v1/position/report/MESH-TEAM-ALPHA"
            "?id=TEST-DEVICE&lat=61.218846&lng=-149.900132"
        )

        assert url == expected, f"Expected '{expected}', got '{url}'"
        print("✓ CalTopo URL building works correctly")

        return True

    except Exception as e:
        print(f"✗ CalTopo URL building test failed: {e}")
        return False


def test_node_mapping_mechanism() -> bool:
    """Test the node ID mapping mechanism."""
    print("\nTesting node ID mapping mechanism...")

    try:
        config = Config.from_file(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        app = GatewayApp(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        app.config = config

        # Test nodeinfo message processing
        nodeinfo_message = {
            "from": 862485920,
            "type": "nodeinfo",
            "payload": {
                "id": "!823a4edc",
                "longname": "TEST-DEVICE",
                "shortname": "TEST"
            }
        }

        app._process_nodeinfo_message(nodeinfo_message, 862485920)

        # Verify mapping was created
        assert "862485920" in app.node_id_mapping
        assert app.node_id_mapping["862485920"] == "!823a4edc"
        print("✓ Nodeinfo message mapping works correctly")

        # Test position message with sender fallback
        position_message = {
            "from": 862481648,
            "sender": "!a4b8c2f0",
            "type": "position",
            "payload": {"latitude_i": 612188460, "longitude_i": -1499001320}
        }

        # Initialize CalTopo reporter to avoid errors
        from caltopo_reporter import CalTopoReporter
        app.caltopo_reporter = CalTopoReporter(config)

        app._process_position_message(position_message, 862481648)

        # Verify fallback mapping was created
        assert "862481648" in app.node_id_mapping
        assert app.node_id_mapping["862481648"] == "!a4b8c2f0"
        print("✓ Position message sender fallback works correctly")

        return True

    except Exception as e:
        print(f"✗ Node mapping mechanism test failed: {e}")
        return False


def test_message_type_handling() -> bool:
    """Test different message type handling."""
    print("\nTesting message type handling...")

    try:
        config = Config.from_file(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        app = GatewayApp(str(PROJECT_ROOT / "config" / "config.yaml.example"))
        app.config = config

        # Test telemetry message
        telemetry_message = {
            "from": 862485920,
            "type": "telemetry",
            "payload": {
                "battery_level": 95,
                "voltage": 4.1,
                "uptime_seconds": 3600
            }
        }

        app._process_telemetry_message(telemetry_message, 862485920)
        print("✓ Telemetry message processing works correctly")

        # Test traceroute message
        traceroute_message = {
            "from": 862485920,
            "type": "traceroute",
            "payload": {
                "route": ["DEVICE1", "DEVICE2"]
            }
        }

        app._process_traceroute_message(traceroute_message, 862485920)
        print("✓ Traceroute message processing works correctly")

        # Test empty type message
        empty_type_message = {
            "from": 862485920,
            "type": "",
            "payload": {}
        }

        # This should be handled gracefully
        app._process_message(empty_type_message)
        print("✓ Empty type message handling works correctly")

        return True

    except Exception as e:
        print(f"✗ Message type handling test failed: {e}")
        return False


def main() -> int:
    """Run all tests."""
    print("Meshtopo Gateway Service - Test Suite")
    print("=" * 50)

    # Setup basic logging
    logging.basicConfig(level=logging.WARNING)

    tests = [
        test_config_loading,
        test_message_processing,
        test_caltopo_url_building,
        test_node_mapping_mechanism,
        test_message_type_handling
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
