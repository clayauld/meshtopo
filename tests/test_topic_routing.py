"""Tests for topic-based multi-tenant routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway_app import GatewayApp


@pytest.fixture
def app_topic():
    app = GatewayApp("dummy.yaml")
    app.config = MagicMock()
    app.config.web.multi_tenant_enabled = True
    app.caltopo_reporter = MagicMock()
    app.caltopo_reporter.send_position_update = AsyncMock(return_value=True)

    # Setup tenants_db with mqtt_channel
    app.tenants_db = {
        "tenant_alpha": {
            "caltopo_connect_key": "alpha_key",
            "mqtt_channel": "Alpha-Channel",
            "nodes": {"!12345678": {"device_id": "ALPHA-NODE"}},
        },
        "tenant_beta": {
            "caltopo_connect_key": "beta_key",
            "mqtt_channel": "Beta-Channel",
            "nodes": {},
        },
    }
    app._tenants_cache = dict(app.tenants_db)
    app.node_id_mapping = {}
    app.callsign_mapping = {}
    app._node_id_cache = {}
    app._callsign_cache = {}
    app.device_states = {}
    app.stats = {
        "messages_received": 0,
        "messages_processed": 0,
        "position_updates_sent": 0,
        "errors": 0,
    }
    return app


def test_extract_channel_from_topic(app_topic):
    """Test channel extraction from various topic formats."""
    assert (
        app_topic._extract_channel_from_topic("msh/US/2/json/LongFast/!12345678")
        == "LongFast"
    )
    assert (
        app_topic._extract_channel_from_topic("msh/EU_868/2/json/TeamA/!abcdef")
        == "TeamA"
    )
    assert (
        app_topic._extract_channel_from_topic(
            "msh/region/2/json/Channel-With-Dashes/!123"
        )
        == "Channel-With-Dashes"
    )
    assert app_topic._extract_channel_from_topic("short/topic") is None
    assert app_topic._extract_channel_from_topic("msh/US/2/json") is None


@pytest.mark.asyncio
async def test_routing_by_channel(app_topic):
    """Test that messages are routed to the tenant matching the topic channel."""
    msg = {
        "from": "123",
        "type": "position",
        "payload": {"latitude_i": 100000000, "longitude_i": 200000000},
    }
    topic = "msh/US/2/json/Alpha-Channel/!0000007b"

    with patch("gateway_app.GatewayApp._resolve_hardware_id", return_value="!12345678"):
        await app_topic._process_message(msg, topic)

    # Should route to tenant_alpha because channel "Alpha-Channel" matches
    app_topic.caltopo_reporter.send_position_update.assert_called_once_with(
        "ALPHA-NODE", 10.0, 20.0, group=None, connect_key="alpha_key"
    )


@pytest.mark.asyncio
async def test_routing_by_channel_case_insensitive(app_topic):
    """Test that channel matching is case-insensitive."""
    msg = {
        "from": "123",
        "type": "position",
        "payload": {"latitude_i": 100000000, "longitude_i": 200000000},
    }
    # Topic has lowercase "alpha-channel", tenant has "Alpha-Channel"
    topic = "msh/US/2/json/alpha-channel/!0000007b"

    with patch("gateway_app.GatewayApp._resolve_hardware_id", return_value="!12345678"):
        await app_topic._process_message(msg, topic)

    app_topic.caltopo_reporter.send_position_update.assert_called_once_with(
        "ALPHA-NODE", 10.0, 20.0, group=None, connect_key="alpha_key"
    )


@pytest.mark.asyncio
async def test_routing_to_unmapped_node_on_matched_channel(app_topic):
    """Test that a node not in 'nodes' is routed if the channel matches."""
    msg = {
        "from": "456",
        "type": "position",
        "payload": {"latitude_i": 300000000, "longitude_i": 400000000},
    }
    # Channel matches tenant_beta, but node !88888888 is not in beta's nodes
    topic = "msh/US/2/json/Beta-Channel/!88888888"

    with patch("gateway_app.GatewayApp._resolve_hardware_id", return_value="!88888888"):
        await app_topic._process_message(msg, topic)

    # Should route to tenant_beta, using hardware_id as callsign (fallback)
    app_topic.caltopo_reporter.send_position_update.assert_called_once_with(
        "!88888888", 30.0, 40.0, group=None, connect_key="beta_key"
    )
