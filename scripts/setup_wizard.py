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
        mqtt_broker = config.get("mqtt", {}).get("broker", "")
        config["mqtt"]["broker"] = (
            input(f"MQTT Broker [{mqtt_broker}]: ") or mqtt_broker
        )
        mqtt_port = config.get("mqtt", {}).get("port", 1883)
        config["mqtt"]["port"] = int(input(f"MQTT Port [{mqtt_port}]: ") or mqtt_port)
        mqtt_username = config.get("mqtt", {}).get("username", "")
        config["mqtt"]["username"] = (
            input(f"MQTT Username [{mqtt_username}]: ") or mqtt_username
        )
        mqtt_pass = config.get("mqtt", {}).get("password", "")
        config["mqtt"]["password"] = getpass("MQTT Password: ") or mqtt_pass

    # Save configuration
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, sort_keys=False)
    print(f"\nConfiguration saved to '{CONFIG_FILE}'.")

    # Mosquitto password file
    if config.get("mqtt_broker", {}).get("enabled", False):
        print("\n--- Internal MQTT Broker Setup ---")
        mqtt_users = config.get("mqtt_broker", {}).get("users", [])
        if not mqtt_users:
            print("No users found in 'mqtt_broker.users'.")
            return

        # Clear the password file
        with open(MOSQUITTO_PASSWD_FILE, "w") as f:
            f.write("")

        for user in mqtt_users:
            username = user.get("username")
            if not username:
                print("Skipping user with no username.")
                continue

            print(f"Setting password for user '{username}'.")
            password = getpass("Password: ")
            if not password:
                print("Password cannot be empty. Skipping user.")
                continue

            try:
                subprocess.run(
                    [
                        "mosquitto_passwd",
                        "-b",
                        MOSQUITTO_PASSWD_FILE,
                        username,
                        password,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Successfully updated password for user '{username}'.")
            except FileNotFoundError:
                print(
                    "ERROR: 'mosquitto_passwd' command not found. "
                    "Is Mosquitto installed and in your PATH?"
                )
                return
            except subprocess.CalledProcessError as e:
                print(
                    f"ERROR: Failed to update password for user '{username}': "
                    f"{e.stderr}"
                )


if __name__ == "__main__":
    main()
