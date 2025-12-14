import logging
from unittest.mock import Mock, patch

import pytest
import requests

from caltopo_reporter import CalTopoReporter


@pytest.fixture
def reporter():
    mock_config = Mock()
    mock_config.caltopo.connect_key = None
    mock_config.caltopo.group = None

    # Suppress logging during tests
    logging.getLogger("caltopo_reporter").setLevel(logging.CRITICAL)

    reporter_instance = CalTopoReporter(mock_config)
    yield reporter_instance
    reporter_instance.close()


def test_init_sets_up_session(reporter):
    assert isinstance(reporter.session, requests.Session)
    assert reporter.timeout == 10


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


@patch("requests.Session.get")
def test_send_to_connect_key_success(mock_get, reporter):
    reporter.config.caltopo.connect_key = "secret_key"
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = reporter._send_to_connect_key("TEST-CALL", 10.0, 20.0)

    assert result
    mock_get.assert_called_once()
    args, _ = mock_get.call_args
    assert "secret_key" in args[0]
    assert "id=TEST-CALL" in args[0]


def test_send_to_connect_key_invalid_key(reporter):
    reporter.config.caltopo.connect_key = "bad key"
    result = reporter._send_to_connect_key("TEST-CALL", 10.0, 20.0)
    assert not result


@patch("requests.Session.get")
def test_send_to_group_success(mock_get, reporter):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = reporter._send_to_group("TEST-CALL", 10.0, 20.0, "my_group")

    assert result
    mock_get.assert_called_once()
    args, _ = mock_get.call_args
    assert "my_group" in args[0]


def test_send_to_group_invalid_group(reporter):
    result = reporter._send_to_group("TEST-CALL", 10.0, 20.0, "bad group")
    assert not result


@patch("requests.Session.get")
def test_make_api_request_errors(mock_get, reporter):
    url = "http://example.com"

    # HTTP 500
    mock_get.return_value.status_code = 500
    mock_get.return_value.text = "Server Error"
    assert not reporter._make_api_request(url, "CALL", "test")

    # Timeout
    mock_get.side_effect = requests.exceptions.Timeout
    assert not reporter._make_api_request(url, "CALL", "test")

    # Connection Error
    mock_get.side_effect = requests.exceptions.ConnectionError
    assert not reporter._make_api_request(url, "CALL", "test")

    # General Request Exception
    mock_get.side_effect = requests.exceptions.RequestException("Boom")
    assert not reporter._make_api_request(url, "CALL", "test")

    # Unexpected Exception
    mock_get.side_effect = Exception("Unexpected")
    assert not reporter._make_api_request(url, "CALL", "test")


@patch("caltopo_reporter.CalTopoReporter._send_to_connect_key")
@patch("caltopo_reporter.CalTopoReporter._send_to_group")
def test_send_position_update_strategies(mock_group, mock_key, reporter):
    # 1. Neither configured
    reporter.config.caltopo.connect_key = None
    reporter.config.caltopo.group = None
    assert not reporter.send_position_update("C", 1, 1)

    # 2. Key only - success
    reporter.config.caltopo.connect_key = "key"
    mock_key.return_value = True
    assert reporter.send_position_update("C", 1, 1)
    mock_key.assert_called()
    mock_group.assert_not_called()

    # 3. Group only - success
    reporter.config.caltopo.connect_key = None
    reporter.config.caltopo.group = "group"
    mock_group.return_value = True
    assert reporter.send_position_update("C", 1, 1)

    # 4. Both configured - one success
    reporter.config.caltopo.connect_key = "key"
    reporter.config.caltopo.group = "group"
    mock_key.return_value = False
    mock_group.return_value = True
    assert reporter.send_position_update("C", 1, 1)

    # 5. Both configured - both fail
    mock_key.return_value = False
    mock_group.return_value = False
    assert not reporter.send_position_update("C", 1, 1)


@patch("caltopo_reporter.CalTopoReporter._test_connect_key_endpoint")
@patch("caltopo_reporter.CalTopoReporter._test_group_endpoint")
def test_test_connection(mock_test_group, mock_test_key, reporter):
    # No config
    reporter.config.caltopo.connect_key = None
    reporter.config.caltopo.group = None
    assert not reporter.test_connection()

    # Key success
    reporter.config.caltopo.connect_key = "key"
    mock_test_key.return_value = True
    assert reporter.test_connection()

    # Key fail
    mock_test_key.return_value = False
    assert not reporter.test_connection()


@patch("requests.Session.get")
def test_endpoint_tests(mock_get, reporter):
    # Connect key test
    reporter.config.caltopo.connect_key = "key"
    mock_get.return_value.status_code = 200
    assert reporter._test_connect_key_endpoint()

    # Group test
    reporter.config.caltopo.connect_key = None
    reporter.config.caltopo.group = "group"
    assert reporter._test_group_endpoint()

    # Exception
    mock_get.side_effect = Exception("Fail")
    assert not reporter._test_group_endpoint()
