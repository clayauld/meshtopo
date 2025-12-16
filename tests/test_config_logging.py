import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from config.config import (
    CalTopoConfig,
    Config,
    FileLoggingConfig,
    LoggingConfig,
    MqttConfig,
)


class TestConfigLogging:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "test.log"
        self.dummy_mqtt = MqttConfig(broker="test")
        self.dummy_caltopo = CalTopoConfig(connect_key="test")

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def test_setup_logging_file_enabled(self):
        """Test logging setup with file logging enabled."""
        config = Config(
            mqtt=self.dummy_mqtt,
            caltopo=self.dummy_caltopo,
            logging=LoggingConfig(
                level="DEBUG",
                file=FileLoggingConfig(
                    enabled=True,
                    path=str(self.log_file),
                    max_size="100KB",
                    backup_count=2,
                ),
            ),
        )

        # Mock logging.basicConfig and RotatingFileHandler
        with (
            patch("logging.basicConfig") as mock_basic_config,
            patch("logging.handlers.RotatingFileHandler") as MockHandler,
        ):

            config.setup_logging()

            # Verify basicConfig was called
            mock_basic_config.assert_called_once()
            _, kwargs = mock_basic_config.call_args
            handlers = kwargs.get("handlers", [])

            # Verify RotatingFileHandler was created and added
            assert any(h == MockHandler.return_value for h in handlers)
            MockHandler.assert_called_with(
                Path(self.log_file), maxBytes=100 * 1024, backupCount=2
            )

            # Verify directory creation
            assert self.log_file.parent.exists()

    def test_setup_logging_max_size_parsing(self):
        """Test parsing of different max_size formats."""
        sizes = {
            "1M": 1024 * 1024,
            "5MB": 5 * 1024 * 1024,
            "500K": 500 * 1024,
            "100KB": 100 * 1024,
            "10000": 10000,
            "invalid": 10 * 1024 * 1024,  # Defaults to 10MB
        }

        for size_str, expected_bytes in sizes.items():
            config = Config(
                mqtt=self.dummy_mqtt,
                caltopo=self.dummy_caltopo,
                logging=LoggingConfig(
                    file=FileLoggingConfig(
                        enabled=True, path=str(self.log_file), max_size=size_str
                    )
                ),
            )

            with (
                patch("logging.basicConfig"),
                patch("logging.handlers.RotatingFileHandler") as MockHandler,
            ):

                config.setup_logging()
                MockHandler.assert_called_with(
                    Path(self.log_file), maxBytes=expected_bytes, backupCount=5
                )

    def test_setup_logging_permission_error(self):
        """Test handling of permission error during log setup."""
        config = Config(
            mqtt=self.dummy_mqtt,
            caltopo=self.dummy_caltopo,
            logging=LoggingConfig(
                file=FileLoggingConfig(enabled=True, path="/root/test.log")
            ),
        )

        with (
            patch("logging.basicConfig") as mock_basic_config,
            patch("pathlib.Path.mkdir", side_effect=PermissionError("Denied")),
        ):

            # Should print error but not crash
            config.setup_logging()

            # basicConfig should still be called, but likely without file handler
            mock_basic_config.assert_called_once()
