"""Tests for multi-tenant routing in GatewayApp."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gateway_app import GatewayApp

@pytest.fixture
def app_multi():
    app = GatewayApp("dummy.yaml")
    app.config = MagicMock()
    app.config.web.multi_tenant_enabled = True
    app.config.devices.unknown_devices_all_tenants = True
    app.caltopo_reporter = MagicMock()
    app.caltopo_reporter.send_position_update = AsyncMock(return_value=True)
    
    # Setup tenants_db
    app.tenants_db = {
        "tenant1": {
            "caltopo_connect_key": "t1_key",
            "nodes": {
                "!12345678": {"device_id": "T1-NODE", "group": "T1-GROUP"}
            }
        },
        "tenant2": {
            "caltopo_connect_key": "t2_key",
            "nodes": {
                "!87654321": {"device_id": "T2-NODE"}
            }
        }
    }
    app.node_id_mapping = {}
    app.callsign_mapping = {}
    app._node_id_cache = {}
    app._callsign_cache = {}
    app.device_states = {}
    return app

@pytest.mark.asyncio
async def test_process_position_targeted_routing(app_multi):
    """Test routing to a specific tenant when device is mapped."""
    msg = {
        "type": "position",
        "payload": {"latitude_i": 100000000, "longitude_i": 200000000}
    }
    # numeric_node_id "305419896" -> hardware_id "!12345678"
    await app_multi._process_position_message(msg, "305419896")
    
    # Should call send_position_update with tenant1's config
    app_multi.caltopo_reporter.send_position_update.assert_called_once_with(
        "T1-NODE", 10.0, 20.0, group="T1-GROUP", connect_key="t1_key"
    )
    assert app_multi.stats["position_updates_sent"] == 1

@pytest.mark.asyncio
async def test_process_position_broadcast_routing(app_multi):
    """Test broadcasting to all tenants when device is unmapped."""
    # Ensure it's not mapped to any tenant
    msg = {
        "type": "position",
        "payload": {"latitude_i": 500000000, "longitude_i": 600000000}
    }
    # Unmapped hardware_id "!abc12345"
    with patch("gateway_app.GatewayApp._resolve_hardware_id", return_value="!abc12345"):
        await app_multi._process_position_message(msg, "999")
    
    # Should be called once for each tenant (tenant1 and tenant2)
    assert app_multi.caltopo_reporter.send_position_update.call_count == 2
    
    # Verify calls
    calls = app_multi.caltopo_reporter.send_position_update.call_args_list
    connect_keys = [c.kwargs.get("connect_key") for c in calls]
    assert "t1_key" in connect_keys
    assert "t2_key" in connect_keys
    
    # Stats should increment for BOTH deliveries
    assert app_multi.stats["position_updates_sent"] == 2

@pytest.mark.asyncio
async def test_process_position_no_connect_key(app_multi):
    """Test routing failure when tenant lacks connect key."""
    app_multi.stats["errors"] = 0
    app_multi.tenants_db["tenant1"]["caltopo_connect_key"] = None
    app_multi.tenants_db["tenant1"]["caltopo_group"] = None
    
    msg = {
        "type": "position",
        "payload": {"latitude_i": 100000000, "longitude_i": 200000000}
    }
    await app_multi._process_position_message(msg, "305419896")
    
    # Should NOT call send_position_update if no key/group
    app_multi.caltopo_reporter.send_position_update.assert_not_called()

@pytest.mark.asyncio
async def test_process_position_unknown_devices_disabled(app_multi):
    """Test that broadcast is skipped if unknown_devices_all_tenants is False."""
    app_multi.web_config["unknown_devices_all_tenants"] = False
    app_multi.config.devices.unknown_devices_all_tenants = False
    
    msg = {
        "type": "position",
        "payload": {"latitude_i": 500000000, "longitude_i": 600000000}
    }
    with patch("gateway_app.GatewayApp._resolve_hardware_id", return_value="!unmapped"):
        await app_multi._process_position_message(msg, "999")
    
    app_multi.caltopo_reporter.send_position_update.assert_not_called()

@pytest.mark.asyncio
async def test_process_nodeinfo_multi_tenant(app_multi):
    """Test nodeinfo processing updates only internal mapping in multi-tenant mode."""
    msg = {
        "type": "nodeinfo",
        "payload": {"id": "!12345678", "longname": "Node Name"}
    }
    app_multi._process_nodeinfo_message(msg, "305419896")
    
    # Should update node_id_mapping
    assert app_multi.node_id_mapping["305419896"] == "!12345678"
    # Should NOT update callsign_mapping (tenants manage their own aliases)
    assert "!12345678" not in app.callsign_mapping
