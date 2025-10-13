#!/usr/bin/env python3
"""
Generate Mosquitto MQTT broker configuration from config.yaml.
"""

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import Config


def generate_mosquitto_password(password: str) -> str:
    """
    Generate Mosquitto password hash.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password in Mosquitto format
    """
    # Mosquitto uses PBKDF2 with SHA512
    import base64
    import hashlib

    # Generate salt (8 bytes)
    salt = os.urandom(8)

    # Generate hash using PBKDF2
    hash_bytes = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 101)

    # Combine salt and hash
    combined = salt + hash_bytes

    # Encode as base64
    return base64.b64encode(combined).decode("ascii")


def generate_mosquitto_config(config_path: str, output_dir: str = None) -> bool:
    """
    Generate Mosquitto configuration files from config.yaml.

    Args:
        config_path: Path to config.yaml file
        output_dir: Output directory (defaults to deploy/)

    Returns:
        bool: True if successful, False otherwise
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "deploy"
    else:
        output_dir = Path(output_dir)

    try:
        # Load configuration
        config = Config.from_file(config_path)

        if not config.mqtt_broker.enabled:
            print("MQTT broker is not enabled in configuration")
            return False

        broker_config = config.mqtt_broker

        # Generate mosquitto.conf from template
        template_path = PROJECT_ROOT / "deploy" / "mosquitto.conf.template"
        if not template_path.exists():
            print(f"Template file not found: {template_path}")
            return False

        with open(template_path, "r") as f:
            template_content = f.read()

        # Simple template substitution (replace {{ broker_config.field }} with values)
        mosquitto_conf = template_content
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.port }}", str(broker_config.port)
        )
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.websocket_port }}", str(broker_config.websocket_port)
        )
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.max_connections }}", str(broker_config.max_connections)
        )
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.allow_anonymous }}",
            str(broker_config.allow_anonymous).lower(),
        )
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.persistence }}", str(broker_config.persistence).lower()
        )
        mosquitto_conf = mosquitto_conf.replace(
            "{{ broker_config.acl_enabled }}", str(broker_config.acl_enabled).lower()
        )

        # Write mosquitto.conf
        mosquitto_conf_path = output_dir / "mosquitto.conf"
        with open(mosquitto_conf_path, "w") as f:
            f.write(mosquitto_conf)
        print(f"Generated mosquitto.conf: {mosquitto_conf_path}")

        # Generate password file if not allowing anonymous access
        if not broker_config.allow_anonymous and broker_config.users:
            passwd_path = output_dir / "passwd"
            with open(passwd_path, "w") as f:
                for user in broker_config.users:
                    if user.username and user.password:
                        hashed_password = generate_mosquitto_password(user.password)
                        f.write(f"{user.username}:{hashed_password}\n")
            print(f"Generated passwd file: {passwd_path}")

            # Generate ACL file if enabled
            if broker_config.acl_enabled:
                acl_path = output_dir / "aclfile"
                with open(acl_path, "w") as f:
                    f.write("# Mosquitto ACL file\n")
                    f.write("# Generated from config.yaml\n\n")

                    for user in broker_config.users:
                        if user.acl == "read":
                            f.write(
                                f"user {user.username}\ntopic read msh/+/+/+/+/+\n\n"
                            )
                        elif user.acl == "write":
                            f.write(
                                f"user {user.username}\ntopic write msh/+/+/+/+/+\n\n"
                            )
                        elif user.acl == "readwrite":
                            f.write(
                                f"user {user.username}\ntopic readwrite msh/+/+/+/+/+\n\n"
                            )

                print(f"Generated ACL file: {acl_path}")

        # Generate docker-compose override if needed
        override_path = output_dir / "docker-compose.override.yml"
        if broker_config.enabled:
            override_content = f"""# Docker Compose override for internal MQTT broker
# Generated from config.yaml - DO NOT EDIT MANUALLY

version: '3.8'

services:
  mosquitto:
    ports:
      - "{broker_config.port}:{broker_config.port}"
      - "{broker_config.websocket_port}:{broker_config.websocket_port}"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_data:/mosquitto/log
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
"""

            if not broker_config.allow_anonymous and broker_config.users:
                override_content += "      - ./passwd:/mosquitto/config/passwd:ro\n"

            if broker_config.acl_enabled:
                override_content += "      - ./aclfile:/mosquitto/config/aclfile:ro\n"

            override_content += """
    healthcheck:
      test: ["CMD", "mosquitto_pub", "-h", "localhost", "-t", "test", "-m", "healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  mosquitto_data:
"""

            with open(override_path, "w") as f:
                f.write(override_content)
            print(f"Generated docker-compose override: {override_path}")

        print("Mosquitto configuration generated successfully!")
        return True

    except Exception as e:
        print(f"Error generating Mosquitto configuration: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Mosquitto MQTT broker configuration"
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        default="config/config.yaml",
        help="Path to config.yaml file (default: config/config.yaml)",
    )
    parser.add_argument(
        "-o", "--output-dir", help="Output directory (default: deploy/)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    config_path = Path(args.config_path)
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)

    success = generate_mosquitto_config(str(config_path), args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
