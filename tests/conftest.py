"""
pytest configuration for Meshtopo Gateway Service tests.

This file configures pytest to work with the project's test structure.
"""

import sys
from pathlib import Path
from typing import Any, List

# Add project root and tests directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = Path(__file__).parent

# Add paths to sys.path for imports
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(TESTS_DIR))


# Configure pytest
def pytest_configure(config: Any) -> None:
    """Configure pytest with project-specific settings."""
    # Add custom markers if needed
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


def pytest_collection_modifyitems(config: Any, items: List[Any]) -> None:
    """Modify test collection to add markers or other modifications."""
    for item in items:
        # Add slow marker to tests that take longer than 5 seconds
        if "reconnect" in item.name or "timeout" in item.name:
            item.add_marker("slow")

        # Add integration marker to tests that require external services
        if "mqtt" in item.name.lower() and "client" in item.name.lower():
            item.add_marker("integration")
