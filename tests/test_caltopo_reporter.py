"""
Tests for CalTopoReporter.

Updated for V2 architecture:
- Tests public API: `send_position_update`, `test_connection`
- Mocks internal `httpx` behavior directly.
- Avoids testing removed private methods.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from caltopo_reporter import CalTopoReporter


@pytest.fixture
def reporter():
    mock_config = Mock()
    mock_config.caltopo.connect_key = None
    mock_config.caltopo.has_connect_key = False
    mock_config.caltopo.group = None
    mock_config.caltopo.has_group = False

    # Suppress logging during tests
    logging.getLogger("caltopo_reporter").setLevel(logging.CRITICAL)

    reporter_instance = CalTopoReporter(mock_config)
    yield reporter_instance
    # Cleanup logic if necessary
    # asyncio.run(reporter_instance.close())


@pytest.fixture
def mock_client():
    client = AsyncMock()
    # Ensure is_closed is False so the reporter doesn't try to replace it
    client.is_closed = False
    return client


@pytest.mark.asyncio
async def test_test_connection_success(reporter, mock_client):
    """Test connectivity check passes when domain is reachable."""
    reporter._client = mock_client
    reporter._owns_client = False

    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    assert await reporter.test_connection()
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_test_connection_failure(reporter, mock_client):
    """Test connectivity check fails on network error."""
    reporter._client = mock_client
    reporter._owns_client = False

    mock_client.get.side_effect = httpx.RequestError("Network Error")

    assert not await reporter.test_connection()


@pytest.mark.asyncio
async def test_send_position_update_no_config(reporter):
    """Test behavior when no destinations are configured."""
    assert not await reporter.send_position_update("User", 10.0, 20.0)


@pytest.mark.asyncio
async def test_send_position_update_connect_key(reporter, mock_client):
    """Test sending to Connect Key endpoint."""
    reporter.config.caltopo.connect_key = "secret_key"
    reporter.config.caltopo.has_connect_key = True
    reporter._client = mock_client
    reporter._owns_client = False

    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    success = await reporter.send_position_update("User", 10.0, 20.0)

    assert success
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert "secret_key" in args[0]
    assert kwargs["json"] == {"id": "User", "lat": 10.0, "lon": 20.0}


@pytest.mark.asyncio
async def test_send_position_update_group(reporter, mock_client):
    """Test sending to Group endpoint."""
    reporter.config.caltopo.group = "my_group"
    reporter.config.caltopo.has_group = True
    reporter._client = mock_client
    reporter._owns_client = False

    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    success = await reporter.send_position_update("User", 10.0, 20.0)

    assert success
    mock_client.post.assert_called_once()
    args, _ = mock_client.post.call_args
    assert "my_group" in args[0]


@pytest.mark.asyncio
async def test_send_position_update_concurrent(reporter, mock_client):
    """Test sending to both Key and Group concurrently."""
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    reporter.config.caltopo.group = "group"
    reporter.config.caltopo.has_group = True
    reporter._client = mock_client
    reporter._owns_client = False

    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    success = await reporter.send_position_update("User", 10.0, 20.0)

    assert success
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_send_position_update_retry_logic(reporter, mock_client):
    """Test that transient errors trigger retries."""
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    reporter._client = mock_client
    reporter._owns_client = False

    # Fail twice, then succeed
    mock_response = Mock()
    mock_response.status_code = 200

    mock_client.post.side_effect = [
        httpx.RequestError("Fail 1"),
        httpx.RequestError("Fail 2"),
        mock_response,
    ]

    # Patch sleep to speed up test
    with patch("asyncio.sleep", new_callable=AsyncMock):
        success = await reporter.send_position_update("User", 10.0, 20.0)

    assert success
    assert mock_client.post.call_count == 3


@pytest.mark.asyncio
async def test_send_position_update_max_retries_exceeded(reporter, mock_client):
    """Test that we fail after max retries."""
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    reporter._client = mock_client
    reporter._owns_client = False

    mock_client.post.side_effect = httpx.RequestError("Persistent Failure")

    # In `src/caltopo_reporter.py`, the loop is `for attempt in range(max_retries):`
    # where max_retries = 3. So it runs for 0, 1, 2. Total 3 attempts.

    with patch("asyncio.sleep", new_callable=AsyncMock):
        success = await reporter.send_position_update("User", 10.0, 20.0)

    assert not success
    assert mock_client.post.call_count == 3


@pytest.mark.asyncio
async def test_close(reporter):
    """Test proper resource cleanup."""
    mock_c = AsyncMock()
    reporter._client = mock_c
    reporter._owns_client = True

    await reporter.close()
    mock_c.aclose.assert_called_once()
