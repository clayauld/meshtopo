#!/usr/bin/env python3
"""
Test script to understand the intended behavior for different api_mode values.
"""

import tempfile
import yaml
from pathlib import Path
from config.config import Config

def test_connect_key_mode_without_group():
    """Test connect_key mode without group (should work)."""
    config_data = {
        "mqtt": {
            "broker": "test.mqtt.com",
            "port": 1883,
            "username": "test",
            "password": "test",
            "topic": "test/topic"
        },
        "caltopo": {
            "connect_key": "valid_key",
            "api_mode": "connect_key"
            # No group specified
        },
        "nodes": {
            "node1": {
                "device_id": "device123"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = Config.from_file(config_path)
        print("✅ PASS: connect_key mode without group works")
        print(f"   connect_key: {config.caltopo.connect_key}")
        print(f"   group: {config.caltopo.group}")
        return True
    except Exception as e:
        print(f"❌ FAIL: connect_key mode without group failed: {e}")
        return False
    finally:
        Path(config_path).unlink()

def test_group_mode_without_connect_key():
    """Test group mode without connect_key (should this work?)."""
    config_data = {
        "mqtt": {
            "broker": "test.mqtt.com",
            "port": 1883,
            "username": "test",
            "password": "test",
            "topic": "test/topic"
        },
        "caltopo": {
            "api_mode": "group",
            "group": "valid_group"
            # No connect_key specified
        },
        "nodes": {
            "node1": {
                "device_id": "device123"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = Config.from_file(config_path)
        print("✅ PASS: group mode without connect_key works")
        print(f"   connect_key: {config.caltopo.connect_key}")
        print(f"   group: {config.caltopo.group}")
        return True
    except Exception as e:
        print(f"❌ FAIL: group mode without connect_key failed: {e}")
        return False
    finally:
        Path(config_path).unlink()

def test_group_mode_with_empty_connect_key():
    """Test group mode with empty connect_key (should this work?)."""
    config_data = {
        "mqtt": {
            "broker": "test.mqtt.com",
            "port": 1883,
            "username": "test",
            "password": "test",
            "topic": "test/topic"
        },
        "caltopo": {
            "connect_key": "",
            "api_mode": "group",
            "group": "valid_group"
        },
        "nodes": {
            "node1": {
                "device_id": "device123"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = Config.from_file(config_path)
        print("✅ PASS: group mode with empty connect_key works")
        print(f"   connect_key: '{config.caltopo.connect_key}'")
        print(f"   group: {config.caltopo.group}")
        return True
    except Exception as e:
        print(f"❌ FAIL: group mode with empty connect_key failed: {e}")
        return False
    finally:
        Path(config_path).unlink()

if __name__ == "__main__":
    print("Testing different api_mode scenarios...")
    print("=" * 50)
    
    test_connect_key_mode_without_group()
    print()
    test_group_mode_without_connect_key()
    print()
    test_group_mode_with_empty_connect_key()