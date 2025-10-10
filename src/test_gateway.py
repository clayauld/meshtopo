#!/usr/bin/env python3
"""
Test script for the Meshtopo gateway service.
"""

import logging
import sys
from pathlib import Path

# Add parent directory and src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Local imports after path modification
from config.config import Config  # noqa: E402
from gateway_app import GatewayApp  # noqa: E402


def test_config_loading() -> bool:
    """Test configuration loading."""
    print("Testing configuration loading...")

    try:
        # Test with example config
        config = Config.from_file("config/config.yaml.example")
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
        config = Config.from_file("config/config.yaml.example")

        # Create gateway app
        app = GatewayApp("config/config.yaml.example")
        app.config = config

        # Initialize CalTopo reporter
        from caltopo_reporter import CalTopoReporter

        app.caltopo_reporter = CalTopoReporter(config)

        # Test position message
        test_message = {
            "fromId": "!823a4edc",
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
        config = Config.from_file("config/config.yaml.example")
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


def main() -> int:
    """Run all tests."""
    print("Meshtopo Gateway Service - Test Suite")
    print("=" * 50)

    # Setup basic logging
    logging.basicConfig(level=logging.WARNING)

    tests = [test_config_loading, test_message_processing, test_caltopo_url_building]

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
