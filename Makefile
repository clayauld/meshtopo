# Meshtopo Gateway Service - Development Makefile

.PHONY: help install test lint format clean docker-build docker-run docker-stop dev-setup

# Default target
help:
	@echo "Meshtopo Gateway Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install dependencies"
	@echo "  dev-setup    Setup development environment"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker containers"
	@echo ""
	@echo "Service:"
	@echo "  run          Run the gateway service"
	@echo "  config       Show configuration help"

# Install dependencies
install:
	pip3 install -r requirements.txt

# Setup development environment
dev-setup: install
	pip3 install -r requirements.txt
	pip3 install black flake8 mypy pytest pytest-cov isort pre-commit
	pre-commit install
	@echo "Development environment setup complete!"

# Run tests
test:
	python3 src/test_gateway.py

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

# Build Docker image
docker-build:
	docker build -t meshtopo .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker containers
docker-stop:
	docker-compose down

# Run the gateway service
run:
	python3 src/gateway.py

# Show configuration help
config:
	@echo "Configuration Help:"
	@echo "1. Copy config.yaml.example to config.yaml:"
	@echo "   cp config/config.yaml.example config/config.yaml"
	@echo ""
	@echo "2. Edit config.yaml with your settings:"
	@echo "   - MQTT broker details"
	@echo "   - CalTopo group ID"
	@echo "   - Node mappings"
	@echo ""
	@echo "3. Run the service:"
	@echo "   make run"
	@echo "   # or"
	@echo "   docker-compose up -d"
