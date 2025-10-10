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

echo "✓ Dependencies installed"

# Create logs directory
mkdir -p logs

# Copy example config if config.yaml doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating configuration file from template..."
    cp config.yaml.example config.yaml
    echo "✓ Configuration file created: config.yaml"
    echo "  Please edit config.yaml with your MQTT and CalTopo settings"
else
    echo "✓ Configuration file already exists"
fi

# Make scripts executable
chmod +x gateway.py test_gateway.py

echo "✓ Scripts made executable"

echo ""
echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your MQTT and CalTopo settings"
echo "2. Run the service: python3 gateway.py"
echo "3. Or use Docker: docker-compose up -d"
echo ""
echo "For more information, see README.md"
