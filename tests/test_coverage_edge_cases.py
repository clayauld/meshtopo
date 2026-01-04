import os
import sys
from importlib import reload
from unittest.mock import patch

import pytest

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_caltopo_reporter_url_validation():
    """
    Test that the module-level validation in caltopo_reporter.py works.
    We need to reload the module to trigger the top-level code.
    """
    # 1. Test Valid URL
    with patch.dict(
        os.environ, {"CALTOPO_API_URL": "https://caltopo.com/api/v1"}, clear=True
    ):
        import caltopo_reporter

        reload(caltopo_reporter)
        # Should not raise

    # 2. Test Invalid URL (hostname mismatch)
    with patch.dict(
        os.environ, {"CALTOPO_API_URL": "https://evil-site.com/api"}, clear=True
    ):
        # Validation is now triggered on __init__, not just import
        # So we need to instantiate it to test validation, OR call the
        # validation function
        # if it's public. But it is private.
        # However, the Config object is required for init.

        # Let's mock the config object
        from unittest.mock import Mock

        mock_config = Mock()

        with pytest.raises(ValueError, match="Hostname must be 'caltopo.com'"):
            # reload(caltopo_reporter) # This might not trigger it if it's in
            # __init__ now
            # Yes, I moved logic to __init__.

            from caltopo_reporter import CalTopoReporter

            CalTopoReporter(mock_config)

    # Reset to a valid state
    with patch.dict(
        os.environ, {"CALTOPO_API_URL": "https://caltopo.com/api/v1"}, clear=True
    ):
        reload(caltopo_reporter)
