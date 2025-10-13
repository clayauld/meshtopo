#!/usr/bin/env python3
"""
User management utility for Meshtopo Gateway Service.
"""

import os
import sys
from pathlib import Path

import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import Config, UserCalTopoCredentials, UserConfig
from src.web_ui.utils.password import hash_password, verify_password


def load_config(config_path="config/config.yaml"):
    """Load configuration from file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {config_path} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {config_path}: {e}")
        sys.exit(1)


def save_config(config_data, config_path="config/config.yaml"):
    """Save configuration to file."""
    try:
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Configuration saved to {config_path}")
    except Exception as e:
        print(f"Error: Failed to save configuration: {e}")
        sys.exit(1)


def list_users(config_data):
    """List all users."""
    users = config_data.get("users", [])
    if not users:
        print("No users configured")
        return

    print(f"Users ({len(users)}):")
    print("-" * 60)
    for i, user in enumerate(users, 1):
        print(f"{i}. Username: {user.get('username', 'N/A')}")
        print(f"   Role: {user.get('role', 'user')}")
        print(
            f"   Has CalTopo credentials: {'Yes' if user.get('caltopo_credentials') else 'No'}"
        )
        if user.get("caltopo_credentials"):
            creds = user["caltopo_credentials"]
            accessible_maps = creds.get("accessible_maps", [])
            print(f"   Accessible maps: {len(accessible_maps)} maps")
        print()


def add_user(config_data):
    """Add a new user."""
    print("Add New User")
    print("=" * 20)

    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required")
        return False

    # Check if user already exists
    existing_users = config_data.get("users", [])
    if any(user.get("username") == username for user in existing_users):
        print(f"Error: User '{username}' already exists")
        return False

    password = input("Password: ").strip()
    if not password:
        print("Error: Password is required")
        return False

    role = input("Role (admin/user, default: user): ").strip().lower()
    if role not in ["admin", "user"]:
        role = "user"

    # Generate password hash
    password_hash = hash_password(password)

    # Ask about CalTopo credentials
    has_caltopo = input("Add CalTopo credentials? (y/N): ").strip().lower()
    caltopo_credentials = None

    if has_caltopo in ["y", "yes"]:
        credential_id = input("CalTopo credential ID: ").strip()
        secret_key = input("CalTopo secret key: ").strip()

        if credential_id and secret_key:
            accessible_maps_input = input(
                "Accessible map IDs (comma-separated, optional): "
            ).strip()
            accessible_maps = [
                m.strip() for m in accessible_maps_input.split(",") if m.strip()
            ]

            caltopo_credentials = {
                "credential_id": credential_id,
                "secret_key": secret_key,
                "accessible_maps": accessible_maps,
            }

    # Create user
    user_data = {"username": username, "password_hash": password_hash, "role": role}

    if caltopo_credentials:
        user_data["caltopo_credentials"] = caltopo_credentials

    # Add to config
    if "users" not in config_data:
        config_data["users"] = []

    config_data["users"].append(user_data)

    print(f"✓ User '{username}' added successfully")
    return True


def remove_user(config_data):
    """Remove a user."""
    users = config_data.get("users", [])
    if not users:
        print("No users to remove")
        return False

    list_users(config_data)

    try:
        choice = int(input("Enter user number to remove (0 to cancel): "))
        if choice == 0:
            return False

        if 1 <= choice <= len(users):
            user = users[choice - 1]
            username = user.get("username", "Unknown")

            confirm = input(f"Remove user '{username}'? (y/N): ").strip().lower()
            if confirm in ["y", "yes"]:
                del users[choice - 1]
                print(f"✓ User '{username}' removed successfully")
                return True
            else:
                print("Operation cancelled")
                return False
        else:
            print("Invalid choice")
            return False
    except ValueError:
        print("Invalid input")
        return False


def change_password(config_data):
    """Change user password."""
    users = config_data.get("users", [])
    if not users:
        print("No users configured")
        return False

    list_users(config_data)

    try:
        choice = int(input("Enter user number to change password (0 to cancel): "))
        if choice == 0:
            return False

        if 1 <= choice <= len(users):
            user = users[choice - 1]
            username = user.get("username", "Unknown")

            password = input(f"New password for '{username}': ").strip()
            if not password:
                print("Error: Password is required")
                return False

            # Generate new password hash
            password_hash = hash_password(password)
            user["password_hash"] = password_hash

            print(f"✓ Password for '{username}' changed successfully")
            return True
        else:
            print("Invalid choice")
            return False
    except ValueError:
        print("Invalid input")
        return False


def generate_password_hash():
    """Generate password hash for manual use."""
    password = input("Enter password to hash: ").strip()
    if not password:
        print("Error: Password is required")
        return

    password_hash = hash_password(password)
    print(f"Password hash: {password_hash}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        print("Meshtopo User Management Utility")
        print("=" * 35)
        print("Commands:")
        print("  list     - List all users")
        print("  add      - Add a new user")
        print("  remove   - Remove a user")
        print("  password - Change user password")
        print("  hash     - Generate password hash")
        print("  interactive - Interactive mode")
        print()
        command = input("Enter command: ").strip().lower()

    if command == "hash":
        generate_password_hash()
        return

    # Load configuration
    config_data = load_config()

    if command == "list":
        list_users(config_data)
    elif command == "add":
        if add_user(config_data):
            save_config(config_data)
    elif command == "remove":
        if remove_user(config_data):
            save_config(config_data)
    elif command == "password":
        if change_password(config_data):
            save_config(config_data)
    elif command == "interactive":
        while True:
            print("\nMeshtopo User Management")
            print("=" * 25)
            print("1. List users")
            print("2. Add user")
            print("3. Remove user")
            print("4. Change password")
            print("5. Generate password hash")
            print("0. Exit")

            choice = input("\nEnter choice: ").strip()

            if choice == "1":
                list_users(config_data)
            elif choice == "2":
                if add_user(config_data):
                    save_config(config_data)
            elif choice == "3":
                if remove_user(config_data):
                    save_config(config_data)
            elif choice == "4":
                if change_password(config_data):
                    save_config(config_data)
            elif choice == "5":
                generate_password_hash()
            elif choice == "0":
                break
            else:
                print("Invalid choice")
    else:
        print(f"Unknown command: {command}")
        print("Use 'python3 scripts/user_manager.py' for interactive mode")


if __name__ == "__main__":
    main()
