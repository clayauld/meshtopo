"""Tests for web UI views."""

import builtins
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from aiohttp import web

from src.web import create_app
from src.web.keys import GATEWAY_APP_KEY


@pytest.fixture(autouse=True)
def mock_csrf_validation():
    """Mock CSRF validation to pass automatically in view tests."""
    with patch("src.web.views.validate_csrf", return_value=True):
        yield


@pytest.fixture
def mock_gateway_app():
    app = MagicMock()
    app.web_config = {}
    app.config.web.admin_password = "default_admin"
    app.config.devices.allow_unknown_devices = False
    app.config.nodes = {}
    app.config.caltopo.connect_key = "test_key"
    app.config.caltopo.group = "test_group"
    app.config.logging.file.path = "/fake/path.log"
    app.stats = {"uptime": 100}
    app.device_states = {}
    app.stop_event = MagicMock()
    return app


import pytest_asyncio

@pytest_asyncio.fixture
async def cli(mock_gateway_app):
    """Fixture to create an aiohttp test client."""
    from aiohttp.test_utils import TestClient, TestServer
    app = await create_app(mock_gateway_app)
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_index_unauthenticated(cli):
    """Test index redirects to login if unauthenticated."""
    resp = await cli.get("/", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/login"


@pytest.mark.asyncio
async def test_index_authenticated(cli):
    """Test index redirects to status if authenticated."""
    await cli.post("/login", data={"password": "default_admin"})
    resp = await cli.get("/", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"


@pytest.mark.asyncio
async def test_login_get(cli):
    """Test login_get returns HTML."""
    resp = await cli.get("/login")
    assert resp.status == 200
    text = await resp.text()
    assert "password" in text.lower() or "<form" in text.lower() or "<html" in text.lower()


@pytest.mark.asyncio
async def test_login_get_authenticated(cli):
    """Test login GET redirects to status if authenticated."""
    await cli.post("/login", data={"password": "default_admin"})
    resp = await cli.get("/login", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"


@pytest.mark.asyncio
async def test_login_post_invalid(cli):
    """Test login post with invalid password."""
    resp = await cli.post("/login", data={"password": "wrong"}, allow_redirects=False)
    assert resp.status == 200
    text = await resp.text()
    assert "Invalid password" in text


@pytest.mark.asyncio
async def test_login_post_valid_config(cli):
    """Test login post with config default password."""
    resp = await cli.post("/login", data={"password": "default_admin"}, allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"


@pytest.mark.asyncio
async def test_login_post_valid_db_hash(mock_gateway_app):
    """Test login post with db admin hash."""
    import bcrypt
    from aiohttp.test_utils import TestClient, TestServer
    salt = bcrypt.gensalt()
    mock_gateway_app.web_config["admin_password_hash"] = bcrypt.hashpw(b"db_admin", salt).decode("utf-8")
    app = await create_app(mock_gateway_app)
    server = TestServer(app)
    cli = TestClient(server)
    await cli.start_server()
    
    resp = await cli.post("/login", data={"password": "db_admin"}, allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/status"
    await cli.close()


@pytest.mark.asyncio
async def test_login_post_valid_env(mock_gateway_app):
    """Test login post with ENV password."""
    from aiohttp.test_utils import TestClient, TestServer
    app = await create_app(mock_gateway_app)
    server = TestServer(app)
    cli = TestClient(server)
    await cli.start_server()
    
    with patch.dict(os.environ, {"WEB_ADMIN_PASSWORD": "env_admin"}):
        resp = await cli.post("/login", data={"password": "env_admin"}, allow_redirects=False)
        assert resp.status == 302
        assert resp.headers["Location"] == "/status"
    await cli.close()


@pytest.mark.asyncio
async def test_logout(cli):
    """Test logout endpoint."""
    await cli.post("/login", data={"password": "default_admin"})
    resp = await cli.get("/status", allow_redirects=False)
    assert resp.status == 200
    
    resp = await cli.get("/logout", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/login"


@pytest.mark.asyncio
async def test_config_get(cli):
    """Test config GET."""
    await cli.post("/login", data={"password": "default_admin"})
    resp = await cli.get("/config")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_config_post(cli):
    """Test config POST."""
    await cli.post("/login", data={"password": "default_admin"})
    
    data = {"team_id": "new_team", "caltopo_connect_key": "new_key", "caltopo_group": "new_group", "allow_unknown_devices": "on", "node_id[]": ["Node1"], "node_device_id[]": ["Dev1"], "node_group[]": ["Group1"], "admin_password": "new_admin_pass"}
    
    resp = await cli.post("/config", data=data, allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/config?success=1"
    
    gateway_app = cli.server.app[GATEWAY_APP_KEY]
    assert gateway_app.web_config["team_id"] == "new_team"
    assert gateway_app.web_config["caltopo_connect_key"] == "new_key"
    assert gateway_app.web_config["allow_unknown_devices"] is True
    assert gateway_app.web_config["nodes"]["Node1"]["device_id"] == "Dev1"
    assert "admin_password_hash" in gateway_app.web_config


@pytest.mark.asyncio
async def test_restart_post(cli):
    """Test restart POST."""
    await cli.post("/login", data={"password": "default_admin"})
    
    resp = await cli.post("/api/restart")
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp["status"] == "success"
    
    gateway_app = cli.server.app[GATEWAY_APP_KEY]
    assert gateway_app.restart_requested is True


@pytest.mark.asyncio
async def test_api_logs_get(cli):
    """Test api_logs_get API."""
    await cli.post("/login", data={"password": "default_admin"})
    
    with patch("src.web.views.os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="log line 1\\nlog line 2")):
        resp = await cli.get("/api/logs")
        assert resp.status == 200
        text = await resp.text()
        assert "log line 1" in text
        assert "log line 2" in text


@pytest.mark.asyncio
async def test_api_logs_get_exception(cli):
    """Test api_logs_get API on file read error."""
    await cli.post("/login", data={"password": "default_admin"})
    
    with patch("src.web.views.os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=PermissionError("denied")):
        resp = await cli.get("/api/logs")
        assert resp.status == 200
        text = await resp.text()
        assert "Error reading logs" in text


@pytest.mark.asyncio
async def test_status_get(cli):
    """Test status page GET."""
    await cli.post("/login", data={"password": "default_admin"})
    
    with patch("src.web.views.os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="log line 1")):
        resp = await cli.get("/status")
        assert resp.status == 200
        text = await resp.text()
        assert "log line 1" in text


@pytest.mark.asyncio
async def test_status_get_exception(cli):
    """Test status page GET on file read error."""
    await cli.post("/login", data={"password": "default_admin"})
    
    with patch("src.web.views.os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=PermissionError("denied")):
        resp = await cli.get("/status")
        assert resp.status == 200
