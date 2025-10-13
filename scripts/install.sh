#!/bin/bash
# Meshtopo Gateway Service Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo -e "${BLUE}Meshtopo Gateway Service - Installation Script${NC}"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    echo "Please install Python 3.9 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.9 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

print_status "Python $PYTHON_VERSION found"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

print_status "pip3 found"

# Install dependencies
echo ""
print_info "Installing Python dependencies..."
pip3 install -r requirements.txt
print_status "Dependencies installed"

# Create necessary directories
echo ""
print_info "Creating directories..."
mkdir -p logs
mkdir -p deploy
print_status "Directories created"

# Copy example config if config.yaml doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo ""
    print_info "Creating configuration file from template..."
    cp config/config.yaml.example config/config.yaml
    print_status "Configuration file created: config/config.yaml"
    echo ""
    print_warning "IMPORTANT: Please edit config/config.yaml with your settings:"
    echo "  - MQTT broker details"
    echo "  - CalTopo connect key"
    echo "  - Node mappings (optional)"
    echo "  - Internal MQTT broker settings (optional)"
else
    print_status "Configuration file already exists"
fi

# Check for Docker and Docker Compose
echo ""
print_info "Checking for Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_status "Docker $DOCKER_VERSION found"

    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_status "Docker Compose $COMPOSE_VERSION found"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker Compose not found. Docker deployment will not be available."
        DOCKER_AVAILABLE=false
    fi
else
    print_warning "Docker not found. Docker deployment will not be available."
    DOCKER_AVAILABLE=false
fi

# Check for mosquitto_passwd (for internal broker)
echo ""
print_info "Checking for Mosquitto tools..."
if command -v mosquitto_passwd &> /dev/null; then
    print_status "mosquitto_passwd found - internal broker setup available"
    MOSQUITTO_AVAILABLE=true
else
    print_warning "mosquitto_passwd not found - internal broker setup will be limited"
    MOSQUITTO_AVAILABLE=false
fi

# Make scripts executable
echo ""
print_info "Making scripts executable..."
chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true
print_status "Scripts made executable"

echo ""
print_status "Installation completed successfully!"
echo ""

# Show next steps
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Edit config/config.yaml with your MQTT and CalTopo settings"
echo "2. Get your CalTopo connect key from your Team Account access URL"
echo "3. Run the service:"

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "   - Docker: make docker-run"
    echo "   - Local:  make run"
else
    echo "   - Local:  make run"
fi

echo ""

# Show optional features
echo -e "${BLUE}Optional Features:${NC}"
if [ "$MOSQUITTO_AVAILABLE" = true ]; then
    echo "• Internal MQTT broker: make setup-broker"
else
    echo "• Internal MQTT broker: Install mosquitto-tools first"
fi

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "• Docker deployment: make docker-run"
fi

echo "• Configuration help: make config"
echo "• Run tests: make test"
echo ""

# Show configuration help
echo -e "${BLUE}Configuration Help:${NC}"
echo "• Copy config.yaml.example to config.yaml: cp config/config.yaml.example config/config.yaml"
echo "• Edit config.yaml with your settings"
echo "• Get CalTopo connect key from: CalTopo Team Account → Trackable Devices → Access URLs"
echo "• For internal MQTT broker: Enable mqtt_broker section in config.yaml"
echo ""

# Show useful commands
echo -e "${BLUE}Useful Commands:${NC}"
echo "• make help          - Show all available commands"
echo "• make config        - Show configuration help"
echo "• make test          - Run tests"
echo "• make run           - Run gateway service"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "• make docker-run    - Run with Docker Compose"
    echo "• make docker-stop   - Stop Docker containers"
fi
if [ "$MOSQUITTO_AVAILABLE" = true ]; then
    echo "• make setup-broker  - Setup internal MQTT broker"
fi
echo ""

print_status "For more information, see README.md"
