import logging
import unittest
from unittest.mock import Mock, patch

import pytest
import requests

from caltopo_reporter import CalTopoReporter


class TestCalTopoReporter(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.caltopo.connect_key = None
        self.mock_config.caltopo.group = None
        self.reporter = CalTopoReporter(self.mock_config)
        # Suppress logging during tests
        logging.getLogger("caltopo_reporter").setLevel(logging.CRITICAL)

    def tearDown(self):
        self.reporter.close()

    def test_init_sets_up_session(self):
        self.assertIsInstance(self.reporter.session, requests.Session)
        self.assertEqual(self.reporter.timeout, 10)

    def test_validate_caltopo_identifier(self):
        # Valid identifiers
        self.assertTrue(self.reporter._is_valid_caltopo_identifier("ValidKey123"))
        self.assertTrue(self.reporter._is_valid_caltopo_identifier("group_name"))

        # Invalid identifiers
        self.assertFalse(self.reporter._is_valid_caltopo_identifier("invalid key"))
        self.assertFalse(self.reporter._is_valid_caltopo_identifier("bad/char"))
        self.assertFalse(self.reporter._is_valid_caltopo_identifier("hack;attempt"))

    def test_validate_and_log_identifier(self):
        with patch.object(self.reporter.logger, "error") as mock_log:
            # Valid
            self.assertTrue(self.reporter._validate_and_log_identifier("valid", "test"))
            mock_log.assert_not_called()

            # Invalid
            self.assertFalse(
                self.reporter._validate_and_log_identifier("in valid", "test")
            )
            mock_log.assert_called_once()

    @patch("requests.Session.get")
    def test_send_to_connect_key_success(self, mock_get):
        self.mock_config.caltopo.connect_key = "secret_key"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.reporter._send_to_connect_key("TEST-CALL", 10.0, 20.0)

        self.assertTrue(result)
        mock_get.assert_called_once()
        args, _ = mock_get.call_args
        self.assertIn("secret_key", args[0])
        self.assertIn("id=TEST-CALL", args[0])

    def test_send_to_connect_key_invalid_key(self):
        self.mock_config.caltopo.connect_key = "bad key"
        result = self.reporter._send_to_connect_key("TEST-CALL", 10.0, 20.0)
        self.assertFalse(result)

    @patch("requests.Session.get")
    def test_send_to_group_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.reporter._send_to_group("TEST-CALL", 10.0, 20.0, "my_group")

        self.assertTrue(result)
        mock_get.assert_called_once()
        args, _ = mock_get.call_args
        self.assertIn("my_group", args[0])

    def test_send_to_group_invalid_group(self):
        result = self.reporter._send_to_group("TEST-CALL", 10.0, 20.0, "bad group")
        self.assertFalse(result)

    @patch("requests.Session.get")
    def test_make_api_request_errors(self, mock_get):
        url = "http://example.com"

        # HTTP 500
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Server Error"
        self.assertFalse(self.reporter._make_api_request(url, "CALL", "test"))

        # Timeout
        mock_get.side_effect = requests.exceptions.Timeout
        self.assertFalse(self.reporter._make_api_request(url, "CALL", "test"))

        # Connection Error
        mock_get.side_effect = requests.exceptions.ConnectionError
        self.assertFalse(self.reporter._make_api_request(url, "CALL", "test"))

        # General Request Exception
        mock_get.side_effect = requests.exceptions.RequestException("Boom")
        self.assertFalse(self.reporter._make_api_request(url, "CALL", "test"))

        # Unexpected Exception
        mock_get.side_effect = Exception("Unexpected")
        self.assertFalse(self.reporter._make_api_request(url, "CALL", "test"))

    @patch("caltopo_reporter.CalTopoReporter._send_to_connect_key")
    @patch("caltopo_reporter.CalTopoReporter._send_to_group")
    def test_send_position_update_strategies(self, mock_group, mock_key):
        # 1. Neither configured
        self.mock_config.caltopo.connect_key = None
        self.mock_config.caltopo.group = None
        self.assertFalse(self.reporter.send_position_update("C", 1, 1))

        # 2. Key only - success
        self.mock_config.caltopo.connect_key = "key"
        mock_key.return_value = True
        self.assertTrue(self.reporter.send_position_update("C", 1, 1))
        mock_key.assert_called()
        mock_group.assert_not_called()

        # 3. Group only - success
        self.mock_config.caltopo.connect_key = None
        self.mock_config.caltopo.group = "group"
        mock_group.return_value = True
        self.assertTrue(self.reporter.send_position_update("C", 1, 1))

        # 4. Both configured - one success
        self.mock_config.caltopo.connect_key = "key"
        self.mock_config.caltopo.group = "group"
        mock_key.return_value = False
        mock_group.return_value = True
        self.assertTrue(self.reporter.send_position_update("C", 1, 1))

        # 5. Both configured - both fail
        mock_key.return_value = False
        mock_group.return_value = False
        self.assertFalse(self.reporter.send_position_update("C", 1, 1))

    @patch("caltopo_reporter.CalTopoReporter._test_connect_key_endpoint")
    @patch("caltopo_reporter.CalTopoReporter._test_group_endpoint")
    def test_test_connection(self, mock_test_group, mock_test_key):
        # No config
        self.mock_config.caltopo.connect_key = None
        self.mock_config.caltopo.group = None
        self.assertFalse(self.reporter.test_connection())

        # Key success
        self.mock_config.caltopo.connect_key = "key"
        mock_test_key.return_value = True
        self.assertTrue(self.reporter.test_connection())

        # Key fail
        mock_test_key.return_value = False
        self.assertFalse(self.reporter.test_connection())

    @patch("requests.Session.get")
    def test_endpoint_tests(self, mock_get):
        # Connect key test
        self.mock_config.caltopo.connect_key = "key"
        mock_get.return_value.status_code = 200
        self.assertTrue(self.reporter._test_connect_key_endpoint())

        # Group test
        self.mock_config.caltopo.connect_key = None
        self.mock_config.caltopo.group = "group"
        self.assertTrue(self.reporter._test_group_endpoint())

        # Exception
        mock_get.side_effect = Exception("Fail")
        self.assertFalse(self.reporter._test_group_endpoint())
