#!/usr/bin/env python3
"""
Test MQTT topic format and region code handling.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestMQTTTopicFormat(unittest.TestCase):
    """Test MQTT topic format and region code handling."""

    def test_region_code_topic_format(self):
        """Test that MQTT topic format uses proper region codes."""
        # Test that config files contain proper region codes
        config_files = [
            "config/config.yaml.example",
            "config/config.yaml.minimal",
            "config/config.yaml.basic",
            "config/config.yaml.docker",
            "config/config.yaml.production",
        ]

        for config_file in config_files:
            config_path = PROJECT_ROOT / config_file
            if config_path.exists():
                with open(config_path, "r") as f:
                    content = f.read()
                    # Check that topic format is correct
                    self.assertIn(
                        "msh/",
                        content,
                        f"Config file {config_file} should contain msh/ topic prefix",
                    )
                    self.assertIn(
                        "/2/json/+/+",
                        content,
                        f"Config file {config_file} should contain /2/json/+/+ topic suffix",
                    )
                    # Check that it uses a specific region code, not placeholder
                    self.assertRegex(
                        content,
                        r"msh/[A-Z_]+/2/json/\+/\+",
                        f"Config file {config_file} should use specific region code",
                    )

    def test_common_region_codes(self):
        """Test that documentation includes common region codes."""
        readme_path = PROJECT_ROOT / "README.md"
        with open(readme_path, "r") as f:
            content = f.read()

        # Check for region code documentation
        self.assertIn("LoRa Region Codes", content)
        self.assertIn("US", content)
        self.assertIn("EU_868", content)
        self.assertIn("ANZ", content)
        self.assertIn("meshtastic.org/docs/configuration/region-by-country/", content)

    def test_design_documentation(self):
        """Test that design document includes region code information."""
        design_path = PROJECT_ROOT / "docs" / "design.md"
        with open(design_path, "r") as f:
            content = f.read()

        # Check for region code documentation
        self.assertIn("msh/REGION/2/json/+/+", content)
        self.assertIn("meshtastic.org/docs/configuration/region-by-country/", content)
        self.assertIn("US", content)
        self.assertIn("EU_868", content)


if __name__ == "__main__":
    unittest.main()
