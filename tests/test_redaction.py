from unittest.mock import MagicMock

import pytest

from src.caltopo_reporter import CalTopoReporter


class TestRedaction:
    """Test secret redaction in CalTopoReporter."""

    @pytest.fixture
    def reporter(self):
        config = MagicMock()
        config.caltopo.connect_key = "SECRET_KEY"
        config.caltopo.has_connect_key = True
        config.caltopo.group = "SECRET_GROUP"
        config.caltopo.has_group = True

        # Mock client to avoid network calls
        client = MagicMock()
        return CalTopoReporter(config, client=client)

    def test_redact_secrets_method(self, reporter):
        """Test the _redact_secrets method directly."""
        # Valid identifier characters
        text = "https://caltopo.com/api/v1/position/report/SECRET_KEY_123?id=FOO"
        redacted = reporter._redact_secrets(text)
        assert (
            redacted == "https://caltopo.com/api/v1/position/report/<REDACTED>?id=FOO"
        )

        # With trailing punctuation
        text = (
            "Error connecting to "
            "https://caltopo.com/api/v1/position/report/SECRET_KEY. Retrying..."
        )
        redacted = reporter._redact_secrets(text)
        assert redacted == (
            "Error connecting to "
            "https://caltopo.com/api/v1/position/report/<REDACTED>. Retrying..."
        )

        # With hyphens
        text = "https://caltopo.com/api/v1/position/report/SECRET-KEY-123"
        redacted = reporter._redact_secrets(text)
        assert redacted == "https://caltopo.com/api/v1/position/report/<REDACTED>"

        # Multiple occurrences? (Should check if regex replaces all)
        text = (
            "Tried https://caltopo.com/api/v1/position/report/KEY1 and "
            "https://caltopo.com/api/v1/position/report/KEY2"
        )
        redacted = reporter._redact_secrets(text)
        assert redacted == (
            "Tried https://caltopo.com/api/v1/position/report/<REDACTED> and "
            "https://caltopo.com/api/v1/position/report/<REDACTED>"
        )

    def test_validate_and_log_identifier_redaction(self, reporter):
        """Test that invalid identifiers are redacted in logs."""
        # Setup logger mock
        reporter.logger = MagicMock()

        # Test with invalid identifier
        invalid_id = "INVALID ID"  # An identifier with a space is guaranteed to be invalid.
        result = reporter._validate_and_log_identifier(invalid_id, "connect_key")

        assert result is False
        reporter.logger.error.assert_called_once()
        args = reporter.logger.error.call_args[0][0]
        assert "<REDACTED>" in args
        assert invalid_id not in args

    @pytest.mark.asyncio
    async def test_make_api_request_exception_redaction(self, reporter):
        """Test that exceptions in _make_api_request are redacted."""
        import httpx

        # Mock client.get to raise an exception with the secret URL
        secret_url = f"{reporter.BASE_URL}/SECRET_KEY"
        reporter.client.get = MagicMock(
            side_effect=httpx.ConnectError(f"Connection failed to {secret_url}")
        )
        reporter.logger = MagicMock()

        # Call the method
        await reporter._make_api_request(
            reporter.client, secret_url, "CALLSIGN", "connect_key"
        )

        # Check logger calls
        # There should be a warning or error log
        # We expect retries, so warning logs first

        # Check all calls to logger
        found_redacted_log = False
        for call in reporter.logger.warning.call_args_list:
            args = call[0][0]
            if "CalTopo API connection/timeout error" in args:
                # The exception message should be redacted
                assert "SECRET_KEY" not in args
                assert "<REDACTED>" in args
                found_redacted_log = True

        # If no warning (maybe max_retries=0?), check error
        if not found_redacted_log:
            for call in reporter.logger.error.call_args_list:
                args = call[0][0]
                if "Unexpected error" in args or "Failed to send" in args:
                    # Depending on where it fails
                    if "SECRET_KEY" not in args and "<REDACTED>" in args:
                        found_redacted_log = True

        # Since we mocked ConnectError, it should be caught in the first except block
        assert (
            found_redacted_log
        ), "Did not find redacted warning log for connection error"
