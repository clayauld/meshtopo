# Meshtopo Gateway Service - Development Makefile

.PHONY: help install test lint format clean docker-build docker-run docker-stop dev-setup setup-broker generate-broker-config

# Default target
help:
	@echo "Meshtopo Gateway Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install dependencies"
	@echo "  dev-setup    Setup development environment"
	@echo "  test         Run all tests"
	@echo "  test-config  Run configuration tests"
	@echo "  test-gateway Run gateway tests"
	@echo "  test-mqtt    Run MQTT topic format tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker images"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker containers"
	@echo ""
	@echo "Service:"
	@echo "  run          Run the gateway service"
	@echo "  config       Show configuration help"
	@echo ""
	@echo "MQTT Broker:"
	@echo "  setup-broker Setup internal MQTT broker"
	@echo "  generate-broker-config Generate broker configuration files"

# Install dependencies
install:
	pip3 install -r requirements.txt

# Setup development environment
dev-setup: install
	pip3 install black flake8 mypy pytest pytest-cov isort pre-commit
	pre-commit install
	@echo "Development environment setup complete!"

# Run tests
test:
	python3 -m pytest tests/ -v

# Run specific test modules
test-config:
	python3 tests/test_config.py

test-gateway:
	python3 tests/test_gateway_app.py

test-mqtt:
	python3 tests/test_mqtt_topic_format.py

# Run linting
lint:
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	mypy . --ignore-missing-imports
	@echo "Linting complete!"

# Format code
format:
	black . --line-length=88 --target-version=py39
	isort . --profile=black --line-length=88
	@echo "Code formatting complete!"

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type f -name "*.log" -delete
	rm -rf htmlcov/
	rm -f .coverage
	rm -f bandit-report.json
	@echo "Cleanup complete!"

# Build Docker images
docker-build:
	docker build -t meshtopo:latest -f deploy/Dockerfile .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker containers
docker-stop:
	docker-compose down

# Run the gateway service
run:
	python3 src/gateway.py

# Setup internal MQTT broker
setup-broker:
	./scripts/setup_broker.sh

# Generate broker configuration files
generate-broker-config:
	python3 scripts/generate_mosquitto_config.py

# Show configuration help
config:
	@echo "Configuration Help:"
	@echo "1. Copy config.yaml.example to config.yaml:"
	@echo "   cp config/config.yaml.example config/config.yaml"
	@echo ""
	@echo "2. Edit config.yaml with your settings:"
	@echo "   - MQTT broker details"
	@echo "   - CalTopo connect key"
	@echo "   - Node mappings (optional)"
	@echo "   - Internal MQTT broker settings (optional)"
	@echo ""
	@echo "3. Run the service:"
	@echo "   make run          # Core gateway only"
	@echo "   make docker-run   # Full stack with Docker"
	@echo ""
	@echo "4. Setup internal MQTT broker:"
	@echo "   make setup-broker # Setup and start internal broker"
	@echo "   make generate-broker-config # Generate broker config files only"
