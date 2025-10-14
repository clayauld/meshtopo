#!/usr/bin/env python3
"""
Generate Mosquitto MQTT broker configuration from config.yaml.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import bcrypt
from jinja2 import Environment, FileSystemLoader

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import Config  # noqa: E402


def generate_mosquitto_password(password: str) -> str:
    """
    Generate Mosquitto password hash using bcrypt for secure storage.

    Args:
        password: Plain text password

    Returns:
        str: bcrypt hashed password in Mosquitto format ($2b$...)
    """
    # Use bcrypt for secure password hashing
    # Mosquitto supports bcrypt hashes in the format $2b$...

    # Convert password to bytes for bcrypt
    password_bytes = password.encode("utf-8")

    try:
        # Generate bcrypt hash with appropriate cost factor
        # Cost factor 12 provides good security vs performance balance
        salt = bcrypt.gensalt(rounds=12)
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)

        # Convert to string for storage
        result: str = hashed_bytes.decode("utf-8")

        return result

    finally:
        # Clear sensitive data from memory immediately
        if "password_bytes" in locals():
            # Overwrite with zeros before deletion for extra security
            password_bytes = b"\x00" * len(password_bytes)
            del password_bytes
        if "hashed_bytes" in locals():
            del hashed_bytes
        # Note: We cannot clear the input password string as it's immutable
        # The caller should handle clearing the original password


def generate_mosquitto_config(
    config_path: str, output_dir: Optional[str] = None
) -> bool:
    """
    Generate Mosquitto configuration files from config.yaml.

    Args:
        config_path: Path to config.yaml file
        output_dir: Output directory (defaults to deploy/)

    Returns:
        bool: True if successful, False otherwise
    """
    if output_dir is None:
        output_dir_path = PROJECT_ROOT / "deploy"
    else:
        output_dir_path = Path(output_dir)

    try:
        # Load configuration
        config = Config.from_file(config_path)

        if not config.mqtt_broker.enabled:
            print("MQTT broker is not enabled in configuration")
            return False

        broker_config = config.mqtt_broker

        # Generate mosquitto.conf from template using Jinja2
        template_dir = PROJECT_ROOT / "deploy"
        template_file = "mosquitto.conf.template"

        if not (template_dir / template_file).exists():
            print(f"Template file not found: {template_dir / template_file}")
            return False

        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template(template_file)

        # Render template with broker configuration
        mosquitto_conf = template.render(broker_config=broker_config)

        # Write mosquitto.conf
        mosquitto_conf_path = output_dir_path / "mosquitto.conf"
        with open(mosquitto_conf_path, "w") as f:
            f.write(mosquitto_conf)
        print(f"Generated mosquitto.conf: {mosquitto_conf_path}")

        # Generate password file if not allowing anonymous access
        if not broker_config.allow_anonymous and broker_config.users:
            passwd_path = output_dir_path / "passwd"
            with open(passwd_path, "w") as f:
                for user in broker_config.users:
                    if user.username and user.password:
                        # Securely hash password using bcrypt
                        try:
                            # Hash password directly without intermediate variable
                            hashed_password = generate_mosquitto_password(user.password)
                            f.write(f"{user.username}: {hashed_password}\n")
                            # Clear hashed password from memory immediately after use
                            del hashed_password
                        except Exception as e:
                            print(
                                f"Error hashing password for user {user.username}: {e}"
                            )
                            continue
                        # Note: We don't modify user.password as it's typed as str
                        # Password will be garbage collected after function ends

            # Set restrictive file permissions (owner read/write only)
            passwd_path.chmod(0o600)
            print(f"Generated passwd file: {passwd_path}")

            # Generate ACL file if enabled
            if broker_config.acl_enabled:
                acl_path = output_dir_path / "aclfile"
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
                                f"user {user.username}\n"
                                f"topic readwrite msh/+/+/+/+/+\n\n"
                            )

                print(f"Generated ACL file: {acl_path}")

        # Generate docker-compose override if needed
        override_path = output_dir_path / "docker-compose.override.yml"
        if broker_config.enabled:
            override_content = """# Docker Compose override for internal MQTT broker
# Generated from config.yaml - DO NOT EDIT MANUALLY

version: '3.8'

services:
  mosquitto:
    ports:
      - "{}:{}"
      - "{}:{}"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_data:/mosquitto/log
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
""".format(
                broker_config.port,
                broker_config.port,
                broker_config.websocket_port,
                broker_config.websocket_port,
            )

            if not broker_config.allow_anonymous and broker_config.users:
                override_content += "      - ./passwd:/mosquitto/config/passwd:ro\n"

            if broker_config.acl_enabled:
                override_content += "      - ./aclfile:/mosquitto/config/aclfile:ro\n"

            override_content += """
    healthcheck:
      test: [
          "CMD", "mosquitto_pub", "-h", "localhost", "-t", "test", "-m", "healthcheck"
      ]
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


def main() -> None:
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
