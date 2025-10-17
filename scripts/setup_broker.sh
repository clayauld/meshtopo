#!/bin/bash
# Meshtopo MQTT Broker Setup Script
# This script sets up the internal Mosquitto MQTT broker based on config.yaml

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIG_FILE="config/config.yaml"
DEPLOY_DIR="deploy"
VERBOSE=false
FORCE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Setup Meshtopo internal MQTT broker based on config.yaml

OPTIONS:
    -c, --config FILE     Configuration file (default: config/config.yaml)
    -d, --deploy-dir DIR  Deploy directory (default: deploy)
    -f, --force          Force regeneration of existing files
    -v, --verbose        Enable verbose output
    -h, --help           Show this help message

EXAMPLES:
    $0                           # Setup with default config
    $0 -c config/config.yaml     # Setup with specific config
    $0 -f -v                     # Force setup with verbose output

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -d|--deploy-dir)
            DEPLOY_DIR="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Check if deploy directory exists
if [[ ! -d "$DEPLOY_DIR" ]]; then
    print_error "Deploy directory not found: $DEPLOY_DIR"
    exit 1
fi

print_status "Setting up Meshtopo MQTT broker..."
print_status "Config file: $CONFIG_FILE"
print_status "Deploy directory: $DEPLOY_DIR"

# Check if Python script exists
SCRIPT_PATH="scripts/generate_mosquitto_config.py"
if [[ ! -f "$SCRIPT_PATH" ]]; then
    print_error "Configuration generator script not found: $SCRIPT_PATH"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if Docker is available (for validation)
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found - cannot validate broker configuration"
fi

# Generate Mosquitto configuration
print_status "Generating Mosquitto configuration..."

# Build command arguments
ARGS=("$CONFIG_FILE")
if [[ "$VERBOSE" == true ]]; then
    ARGS+=("-v")
fi
if [[ "$DEPLOY_DIR" != "deploy" ]]; then
    ARGS+=("-o" "$DEPLOY_DIR")
fi

# Run the configuration generator
if python3 "$SCRIPT_PATH" "${ARGS[@]}"; then
    print_success "Mosquitto configuration generated successfully"
else
    print_error "Failed to generate Mosquitto configuration"
    exit 1
fi

# Check if broker is enabled in config
if python3 -c "
import sys
sys.path.insert(0, '.')
from config.config import Config
config = Config.from_file('$CONFIG_FILE')
if not config.mqtt_broker.enabled:
    print('Broker not enabled in configuration')
    sys.exit(1)
" 2>/dev/null; then
    print_status "MQTT broker is enabled in configuration"
else
    print_warning "MQTT broker is not enabled in configuration"
    print_status "To enable the broker, set mqtt_broker.enabled: true in $CONFIG_FILE"
    exit 0
fi

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    print_status "Docker Compose found - checking broker service..."

    # Check if broker service is running
    if docker-compose -f "$DEPLOY_DIR/docker-compose.yml" ps mosquitto 2>/dev/null | grep -q "Up"; then
        print_status "Mosquitto broker is already running"

        if [[ "$FORCE" == true ]]; then
            print_status "Force mode enabled - restarting broker service..."
            docker-compose -f "$DEPLOY_DIR/docker-compose.yml" restart mosquitto
            print_success "Broker service restarted"
        else
            print_status "Broker is running. Use -f to force restart."
        fi
    else
        print_status "Starting Mosquitto broker service..."
        docker-compose -f "$DEPLOY_DIR/docker-compose.yml" up -d mosquitto
        print_success "Broker service started"
    fi

    # Wait for broker to be ready
    print_status "Waiting for broker to be ready..."
    sleep 5

    # Test broker connectivity
    if command -v mosquitto_pub &> /dev/null; then
        print_status "Testing broker connectivity..."
        if mosquitto_pub -h localhost -t "test/setup" -m "test" -q 1 2>/dev/null; then
            print_success "Broker connectivity test passed"
        else
            print_warning "Broker connectivity test failed - broker may still be starting"
        fi
    else
        print_warning "mosquitto_pub not found - skipping connectivity test"
    fi

else
    print_warning "Docker Compose not found"
    print_status "Generated configuration files:"
    print_status "  - $DEPLOY_DIR/mosquitto.conf"
    if [[ -f "$DEPLOY_DIR/passwd" ]]; then
        print_status "  - $DEPLOY_DIR/passwd"
    fi
    if [[ -f "$DEPLOY_DIR/docker-compose.override.yml" ]]; then
        print_status "  - $DEPLOY_DIR/docker-compose.override.yml"
    fi
    print_status "Run 'docker-compose up -d mosquitto' to start the broker"
fi

print_success "MQTT broker setup completed!"
print_status "Next steps:"
print_status "  1. Verify broker is running: docker-compose ps"
print_status "  2. Test connectivity: mosquitto_pub -h localhost -t 'test' -m 'hello'"
print_status "  3. Start gateway: docker-compose up -d meshtopo-gateway"
