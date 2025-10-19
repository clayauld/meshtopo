#!/usr/bin/env python3

import os
import shutil
import subprocess
from getpass import getpass

import yaml

# Constants
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
CONFIG_TEMPLATE = os.path.join(CONFIG_DIR, "config.yaml.basic")
MOSQUITTO_PASSWD_FILE = "deploy/passwd"


def main() -> None:
    """The main function for the setup wizard."""
    print("--- Meshtopo Setup Wizard ---")

    # Initialize configuration
    if not os.path.exists(CONFIG_FILE):
        print(f"'{CONFIG_FILE}' not found.")
        try:
            shutil.copy(CONFIG_TEMPLATE, CONFIG_FILE)
            print(f"Created '{CONFIG_FILE}' from template.")
        except FileNotFoundError:
            print(f"ERROR: Template '{CONFIG_TEMPLATE}' not found.")
            return
    else:
        print(f"Found existing configuration file at '{CONFIG_FILE}'.")

    # Load configuration
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)

    # Interactive prompts
    print("\nPlease provide the following information:")

    # CalTopo
    caltopo_key = config.get("caltopo", {}).get("connect_key", "")
    config["caltopo"]["connect_key"] = (
        input(f"Enter your CalTopo 'Connect Key' [{caltopo_key}]: ") or caltopo_key
    )

    # MQTT Broker (external)
    if not config.get("mqtt_broker", {}).get("enabled", False):
        print("\n--- External MQTT Broker ---")
        mqtt_host = config.get("mqtt", {}).get("host", "")
        config["mqtt"]["host"] = input(f"MQTT Host [{mqtt_host}]: ") or mqtt_host
        mqtt_port = config.get("mqtt", {}).get("port", 1883)
        config["mqtt"]["port"] = int(
            input(f"MQTT Port [{mqtt_port}]: ") or mqtt_port
        )
        mqtt_user = config.get("mqtt", {}).get("user", "")
        config["mqtt"]["user"] = input(f"MQTT User [{mqtt_user}]: ") or mqtt_user
        mqtt_pass = config.get("mqtt", {}).get("password", "")
        config["mqtt"]["password"] = getpass("MQTT Password: ") or mqtt_pass

    # Save configuration
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, sort_keys=False)
    print(f"\nConfiguration saved to '{CONFIG_FILE}'.")

    # Mosquitto password file
    if config.get("mqtt_broker", {}).get("enabled", False):
        print("\n--- Internal MQTT Broker Setup ---")
        mqtt_user = config.get("mqtt_broker", {}).get("user")
        if not mqtt_user:
            print(
                "ERROR: 'mqtt_broker.user' not set in config. "
                "Cannot create password file."
            )
            return

        print("Please set a password for the internal MQTT broker.")
        mqtt_password = getpass(f"Password for user '{mqtt_user}': ")
        if not mqtt_password:
            print("Password cannot be empty.")
            return

        # Create the password file
        with open(MOSQUITTO_PASSWD_FILE, "w") as f:
            f.write("")  # Clear the file

        try:
            subprocess.run(
                [
                    "mosquitto_passwd",
                    "-b",
                    MOSQUITTO_PASSWD_FILE,
                    mqtt_user,
                    mqtt_password,
                ],
                check=True,
                capture_output=True,
                text=.True,
            )
            print(f"Successfully created password file at '{MOSQUITTO_PASSWD_FILE}'.")
        except FileNotFoundError:
            print(
                "ERROR: 'mosquitto_passwd' command not found. "
                "Is Mosquitto installed and in your PATH?"
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create password file: {e.stderr}")


if __name__ == "__main__":
    main()
