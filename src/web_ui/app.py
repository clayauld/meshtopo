"""
Main application entry point for the Meshtopo web UI.
"""

import logging
import sys
from pathlib import Path

from . import create_app

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the web UI application."""
    try:
        # Create Flask app
        app = create_app()

        # Get configuration
        config = app.config["MESHTOPO_CONFIG"]

        logger.info(f"Starting Meshtopo web UI on {config.web_ui.host}:{config.web_ui.port}")

        # Run the application
        app.run(
            host=config.web_ui.host,
            port=config.web_ui.port,
            debug=False,
            threaded=True,
        )

    except Exception as e:
        logger.error(f"Failed to start web UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
