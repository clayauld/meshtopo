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
    # No close needed as we don't hold session, but good practice if we did
    # asyncio.run(reporter_instance.close()) # Not easy in fixture yield
    # For now we assume close is no-op or handled


@pytest.fixture
def mock_client():
    client = AsyncMock()
    # Mock context manager
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return client


def test_validate_caltopo_identifier(reporter):
    # Valid identifiers
    assert reporter._is_valid_caltopo_identifier("ValidKey123")
    assert reporter._is_valid_caltopo_identifier("group_name")

    # Invalid identifiers
    assert not reporter._is_valid_caltopo_identifier("invalid key")
    assert not reporter._is_valid_caltopo_identifier("bad/char")
    assert not reporter._is_valid_caltopo_identifier("hack;attempt")


def test_validate_and_log_identifier(reporter):
    with patch.object(reporter.logger, "error") as mock_log:
        # Valid
        assert reporter._validate_and_log_identifier("valid", "test")
        mock_log.assert_not_called()

        # Invalid
        assert not reporter._validate_and_log_identifier("in valid", "test")
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_send_to_connect_key_success(reporter, mock_client):
    reporter.config.caltopo.connect_key = "secret_key"
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    result = await reporter._send_to_connect_key(mock_client, "TEST-CALL", 10.0, 20.0)

    assert result
    mock_client.get.assert_called_once()
    args, _ = mock_client.get.call_args
    assert "secret_key" in args[0]
    assert "id=TEST-CALL" in args[0]


@pytest.mark.asyncio
async def test_send_to_connect_key_invalid_key(reporter, mock_client):
    reporter.config.caltopo.connect_key = "bad key"
    result = await reporter._send_to_connect_key(mock_client, "TEST-CALL", 10.0, 20.0)
    assert not result


@pytest.mark.asyncio
async def test_send_to_group_success(reporter, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    result = await reporter._send_to_group(
        mock_client, "TEST-CALL", 10.0, 20.0, "my_group"
    )

    assert result
    mock_client.get.assert_called_once()
    args, _ = mock_client.get.call_args
    assert "my_group" in args[0]


@pytest.mark.asyncio
async def test_send_to_group_invalid_group(reporter, mock_client):
    result = await reporter._send_to_group(
        mock_client, "TEST-CALL", 10.0, 20.0, "bad group"
    )
    assert not result


@pytest.mark.asyncio
async def test_make_api_request_errors(reporter, mock_client):
    url = "http://example.com"

    # HTTP 500
    mock_client.get.return_value.status_code = 500
    mock_client.get.return_value.text = "Server Error"
    assert not await reporter._make_api_request(mock_client, url, "CALL", "test")

    # Timeout
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    assert not await reporter._make_api_request(mock_client, url, "CALL", "test")

    # Connection Error
    mock_client.get.side_effect = httpx.ConnectError("Connection Error")
    assert not await reporter._make_api_request(mock_client, url, "CALL", "test")

    # Unexpected Exception
    mock_client.get.side_effect = Exception("Unexpected")
    assert not await reporter._make_api_request(mock_client, url, "CALL", "test")


@patch("httpx.AsyncClient")
@pytest.mark.asyncio
async def test_send_position_update_strategies(mock_client_cls, reporter):
    # Verify logic using mocks for internal methods would be better,
    # but since we create client inside, we mock the class.
    mock_instance = AsyncMock()
    mock_instance.__aenter__.return_value = mock_instance
    mock_instance.__aexit__.return_value = None
    mock_client_cls.return_value = mock_instance

    # Mock return values for get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_instance.get.return_value = mock_response

    # 1. Neither configured
    # Defaults are already None/False from fixture
    assert not await reporter.send_position_update("C", 1, 1)

    # 2. Key only - success
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    reporter.config.caltopo.group = None
    reporter.config.caltopo.has_group = False

    assert await reporter.send_position_update("C", 1, 1)

    # 3. Group only - success
    reporter.config.caltopo.connect_key = None
    reporter.config.caltopo.has_connect_key = False
    reporter.config.caltopo.group = "group"
    reporter.config.caltopo.has_group = True

    assert await reporter.send_position_update("C", 1, 1)

    # 4. Both configured - one success (we simulate success on both calls here
    # essentially)
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    reporter.config.caltopo.group = "group"
    reporter.config.caltopo.has_group = True

    # To simulate partial failure we'd need side_effects on get based on URL

    assert await reporter.send_position_update("C", 1, 1)


@patch("httpx.AsyncClient")
@pytest.mark.asyncio
async def test_test_connection(mock_client_cls, reporter):
    mock_instance = AsyncMock()
    mock_instance.__aenter__.return_value = mock_instance
    mock_instance.__aexit__.return_value = None
    mock_client_cls.return_value = mock_instance

    mock_response = Mock()
    mock_response.status_code = 200
    mock_instance.get.return_value = mock_response

    # No config
    reporter.config.caltopo.has_connect_key = False
    reporter.config.caltopo.has_group = False
    assert not await reporter.test_connection()

    # Key success
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.has_connect_key = True
    assert await reporter.test_connection()


@pytest.mark.asyncio
async def test_make_api_request_network_error(reporter, mock_client):
    """Test handling of network errors in _make_api_request."""
    # Mock httpx.AsyncClient to raise RequestError
    mock_client.get.side_effect = httpx.RequestError("Network down")

    # Should return False on exception
    result = await reporter._make_api_request(
        mock_client, "http://test.com", "TEST-CALLSIGN", "test_endpoint"
    )
    assert result is False


@pytest.mark.asyncio
async def test_make_api_request_http_error_404(reporter, mock_client):
    """Test handling of HTTP errors (e.g. 404)."""
    # Mock httpx response with error status
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    mock_client.get.return_value = mock_response

    # Should return False on exception/error status
    result = await reporter._make_api_request(
        mock_client, "http://test.com", "TEST-CALLSIGN", "test_endpoint"
    )
    assert result is False


@pytest.mark.asyncio
async def test_matches_url_pattern():
    from caltopo_reporter import _matches_url_pattern

    assert _matches_url_pattern("http://localhost:8080/api", "http://localhost:8080/*")
    assert _matches_url_pattern("http://other:8080/api", "http://*:8080/*")
    assert not _matches_url_pattern("http://other:8080/api", "http://localhost:8080/*")


@pytest.mark.asyncio
async def test_close(reporter):
    # Setup a mock client
    mock_c = AsyncMock()
    reporter.client = mock_c
    reporter._owns_client = True
    await reporter.close()
    mock_c.aclose.assert_called_once()
    assert reporter.client is None


@pytest.mark.asyncio
async def test_test_connection_no_tasks(reporter):
    reporter.config.caltopo.has_connect_key = False
    reporter.config.caltopo.has_group = False
    assert not await reporter.test_connection()


@pytest.mark.asyncio
async def test_test_connection_group_endpoint(reporter, mock_client):
    reporter.config.caltopo.has_connect_key = False
    reporter.config.caltopo.has_group = True
    reporter.config.caltopo.group = "test_group"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    reporter.client = mock_client
    assert await reporter.test_connection()
    mock_client.get.assert_called_once()
    assert "test_group" in mock_client.get.call_args[0][0]


@pytest.mark.asyncio
async def test_test_connection_failure(reporter, mock_client):
    reporter.config.caltopo.has_connect_key = True
    reporter.config.caltopo.connect_key = "key"

    mock_response = Mock()
    mock_response.status_code = 500
    # In test_connection, it just checks if it gets ANY response for reachability
    # Wait, the current implementation says "Any response (even 4xx/5xx)
    # means we can reach the API"
    # But wait, let's check the code.

    mock_client.get.side_effect = Exception("Connection Failed")
    reporter.client = mock_client
    assert not await reporter.test_connection()


@pytest.mark.asyncio
async def test_send_position_update_no_client_fail(reporter):
    # This covers the RuntimeError case if start() fails to sets self.client
    # which is hard to trigger unless we mock start or subclass.
    # But we can mock self.client to be None after start() call if we are tricky.
    with patch.object(reporter, "start", AsyncMock()):
        reporter.client = None
        with pytest.raises(
            RuntimeError, match="httpx.AsyncClient failed to initialize"
        ):
            await reporter.send_position_update("C", 1, 1)

    with patch.object(reporter, "start", AsyncMock()):
        reporter.client = None
        with pytest.raises(
            RuntimeError, match="httpx.AsyncClient failed to initialize"
        ):
            await reporter.test_connection()


@pytest.mark.asyncio
async def test_test_connect_key_endpoint_invalid_id(reporter, mock_client):
    reporter.config.caltopo.connect_key = "invalid id"
    assert not await reporter._test_connect_key_endpoint(mock_client)


@pytest.mark.asyncio
async def test_test_group_endpoint_invalid_id(reporter, mock_client):
    reporter.config.caltopo.group = "invalid id"
    assert not await reporter._test_group_endpoint(mock_client)


@pytest.mark.asyncio
async def test_test_group_endpoint_exception(reporter, mock_client):
    reporter.config.caltopo.group = "group"
    mock_client.get.side_effect = Exception("error")
    assert not await reporter._test_group_endpoint(mock_client)
