"""Tests for multi-tenant web UI views."""

from unittest.mock import MagicMock, patch

import bcrypt
import pytest
import pytest_asyncio

from src.web import create_app


@pytest.fixture
def mock_gateway_app_multi():
    app = MagicMock()
    app.config.web.admin_password = "default_admin"
    app.config.web.multi_tenant_enabled = True
    app.config.devices.allow_unknown_devices = False
    app.config.devices.unknown_devices_all_tenants = False
    app.config.nodes = {}
    app.stats = {"uptime": 100}
    app.device_states = {"!abc12345": {"longname": "Unmapped Node"}}
    app.web_config = {"unknown_devices_all_tenants": False}

    # Setup tenants_db
    salt = bcrypt.gensalt()
    hash_val = bcrypt.hashpw(b"tenant_pass", salt).decode("utf-8")
    app.tenants_db = {
        "tenant1": {
            "password_hash": hash_val,
            "caltopo_connect_key": "t1_key",
            "nodes": {"!12345678": {"device_id": "T1-NODE", "group": "T1-GROUP"}},
        }
    }
    return app


@pytest_asyncio.fixture
async def cli_multi(mock_gateway_app_multi):
    from aiohttp.test_utils import TestClient, TestServer

    app = await create_app(mock_gateway_app_multi)
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_login_tenant_success(cli_multi):
    """Test successful tenant login."""
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/login",
            data={"username": "tenant1", "password": "tenant_pass"},
            allow_redirects=False,
        )
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"


@pytest.mark.asyncio
async def test_login_tenant_invalid(cli_multi):
    """Test tenant login with wrong password."""
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/login",
            data={"username": "tenant1", "password": "wrong"},
            allow_redirects=False,
        )
    assert resp.status == 200
    text = await resp.text()
    assert "Invalid credentials" in text


@pytest.mark.asyncio
async def test_config_get_superuser_multi(cli_multi):
    """Test config GET as superuser with multi-tenant enabled."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "admin", "password": "default_admin"}
        )
    resp = await cli_multi.get("/config")
    assert resp.status == 200
    text = await resp.text()
    assert "tenant1" in text
    assert "T1-NODE" in text
    assert "Unmapped Node" in text


@pytest.mark.asyncio
async def test_config_get_tenant_view(cli_multi):
    """Test config GET as a regular tenant."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "tenant1", "password": "tenant_pass"}
        )
    resp = await cli_multi.get("/config")
    assert resp.status == 200
    text = await resp.text()
    assert "T1-NODE" in text
    # Should NOT see other tenants or unmapped global nodes as a tenant
    assert "Unmapped Node" not in text


@pytest.mark.asyncio
async def test_admin_panel_get(cli_multi):
    """Test admin panel GET access."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "admin", "password": "default_admin"}
        )
    resp = await cli_multi.get("/admin")
    assert resp.status == 200
    text = await resp.text()
    assert "User Management" in text
    assert "tenant1" in text


@pytest.mark.asyncio
async def test_admin_panel_post_new_tenant(cli_multi, mock_gateway_app_multi):
    """Test creating a new tenant via admin panel."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "admin", "password": "default_admin"}
        )
    # Mock validate_csrf for this test
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/admin",
            data={
                "new_username": "tenant2",
                "new_password": "pass2",
                "new_caltopo_key": "key2",
                "new_caltopo_group": "group2",
            },
            allow_redirects=False,
        )

        assert resp.status == 302
        assert "tenant2" in mock_gateway_app_multi.tenants_db
        assert (
            mock_gateway_app_multi.tenants_db["tenant2"]["caltopo_connect_key"]
            == "key2"
        )


@pytest.mark.asyncio
async def test_admin_panel_post_delete_tenant(cli_multi, mock_gateway_app_multi):
    """Test deleting a tenant via admin panel."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "admin", "password": "default_admin"}
        )
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/admin", data={"delete_username": "tenant1"}, allow_redirects=False
        )

        assert resp.status == 302
        assert "tenant1" not in mock_gateway_app_multi.tenants_db


@pytest.mark.asyncio
async def test_tenant_config_post(cli_multi, mock_gateway_app_multi):
    """Test tenant updating their own configuration."""
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "tenant1", "password": "tenant_pass"}
        )
    with patch("src.web.views.validate_csrf", return_value=True):
        data = {
            "caltopo_connect_key": "updated_key",
            "node_id[]": ["!newhw"],
            "node_device_id[]": ["NEWALIAS"],
        }
        resp = await cli_multi.post("/config", data=data, allow_redirects=False)
        assert resp.status == 302

        tenant_cfg = mock_gateway_app_multi.tenants_db["tenant1"]
        assert tenant_cfg["caltopo_connect_key"] == "updated_key"
        assert tenant_cfg["nodes"]["!newhw"]["device_id"] == "NEWALIAS"


@pytest.mark.asyncio
async def test_tenant_change_password(cli_multi, mock_gateway_app_multi):
    """Test that a tenant can change their own password and then log in."""
    # 1. Log in with old password
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post(
            "/login", data={"username": "tenant1", "password": "tenant_pass"}
        )

    # 2. Change password to 'new_pass'
    with patch("src.web.views.validate_csrf", return_value=True):
        await cli_multi.post("/config", data={"new_password": "new_pass"})

    # Check that it's updated in the mock DB
    new_hash = mock_gateway_app_multi.tenants_db["tenant1"]["password_hash"]
    assert bcrypt.checkpw(b"new_pass", new_hash.encode("utf-8"))

    # 3. Log out
    await cli_multi.get("/logout")

    # 4. Try logging in with the old password (should fail)
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/login",
            data={"username": "tenant1", "password": "tenant_pass"},
            allow_redirects=False,
        )
    assert resp.status == 200  # Login page with error

    # 5. Log in with the new password (should succeed)
    with patch("src.web.views.validate_csrf", return_value=True):
        resp = await cli_multi.post(
            "/login",
            data={"username": "tenant1", "password": "new_pass"},
            allow_redirects=False,
        )
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"
