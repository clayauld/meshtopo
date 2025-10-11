#!/bin/bash
# Meshtopo Gateway Service Installation Script

set -e

echo "Meshtopo Gateway Service - Installation Script"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python 3.9 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install web UI dependencies if web UI is enabled
if [ -f "requirements-web.txt" ]; then
    echo "Installing web UI dependencies..."
    pip3 install -r requirements-web.txt
fi

echo "✓ Dependencies installed"

# Create logs directory
mkdir -p logs

# Copy example config if config.yaml doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo "Creating configuration file from template..."
    cp config/config.yaml.example config/config.yaml
    echo "✓ Configuration file created: config/config.yaml"
    echo "  Please edit config/config.yaml with your MQTT and CalTopo settings"

    # Prompt for initial admin user setup
    echo ""
    echo "Initial Admin User Setup"
    echo "======================="
    read -p "Enter admin username (default: admin): " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

    read -s -p "Enter admin password: " ADMIN_PASSWORD
    echo ""

    if [ -n "$ADMIN_PASSWORD" ]; then
        echo "Generating password hash..."
        PASSWORD_HASH=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from web_ui.utils.password import hash_password
print(hash_password('$ADMIN_PASSWORD'))
")

        echo "✓ Password hash generated"
        echo ""
        echo "IMPORTANT: Add this user to your config/config.yaml:"
        echo "users:"
        echo "  - username: \"$ADMIN_USERNAME\""
        echo "    password_hash: \"$PASSWORD_HASH\""
        echo "    role: \"admin\""
        echo "    caltopo_credentials:"
        echo "      credential_id: \"\""
        echo "      secret_key: \"\""
        echo "      accessible_maps: []"
        echo ""
    else
        echo "No password provided. You can add users later using the password utility:"
        echo "python3 src/web_ui/utils/password.py 'your_password'"
    fi
else
    echo "✓ Configuration file already exists"
fi

# Make scripts executable
chmod +x src/gateway.py src/test_gateway.py

echo "✓ Scripts made executable"

echo ""
echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config/config.yaml with your MQTT and CalTopo settings"
echo "2. Add users to the users section in config.yaml"
echo "3. Generate password hashes using: python3 src/web_ui/utils/password.py 'password'"
echo "4. Run the service:"
echo "   - Core only: python3 src/gateway.py"
echo "   - With web UI: python3 src/web_ui/app.py"
echo "   - Or use Docker: docker-compose up -d"
echo ""
echo "For more information, see README.md"
