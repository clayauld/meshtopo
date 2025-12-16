from unittest.mock import Mock, patch

from gateway import main


def test_main():
    """Test main entry point."""
    with (
        patch("gateway.GatewayApp") as MockApp,
        patch("asyncio.run") as mock_run,
        patch("gateway.Path.exists", return_value=True),
    ):

        mock_app_instance = MockApp.return_value
        # Use Mock instead of AsyncMock for start() because we mock asyncio.run
        # and thus won't actually await the coroutine.
        mock_app_instance.start = Mock()

        main()

        # Verify app was initialized and started
        MockApp.assert_called_once()
        mock_run.assert_called_once()


@patch("sys.exit")
def test_main_default_args(mock_exit):
    """Test main with default arguments (no sys.argv args)."""
    with (
        patch("gateway.GatewayApp") as MockApp,
        patch("asyncio.run") as mock_run,
        patch("gateway.Path.exists", return_value=True),
        patch("sys.argv", ["gateway.py"]),
    ):
        # start() should return a non-coroutine since we mock asyncio.run
        MockApp.return_value.start = Mock()

        main()

        MockApp.assert_called_with("config/config.yaml")
        mock_run.assert_called_once()


@patch("sys.exit")
def test_main_keyboard_interrupt(mock_exit):
    """Test main handling KeyboardInterrupt."""
    with (
        patch("gateway.GatewayApp"),
        patch("asyncio.run", side_effect=KeyboardInterrupt),
        patch("gateway.Path.exists", return_value=True),
        patch("sys.argv", ["gateway.py", "test_config.yaml"]),
    ):

        main()

        # Should catch interrupt and print message, not sys.exit(1)
        mock_exit.assert_not_called()


@patch("sys.exit")
def test_main_fatal_error(mock_exit):
    """Test main handling generic exception."""
    with (
        patch("gateway.GatewayApp") as MockApp,
        patch("asyncio.run", side_effect=Exception("Boom")),
        patch("gateway.Path.exists", return_value=True),
        patch("sys.argv", ["gateway.py", "test_config.yaml"]),
    ):
        # Ensure start() returns a non-coroutine to avoid RuntimeWarning about
        # unawaited coroutine when asyncio.run raises exception immediately.
        MockApp.return_value.start.return_value = None

        main()

        mock_exit.assert_called_with(1)
