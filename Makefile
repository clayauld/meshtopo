# Meshtopo Gateway Service - Development Makefile

.PHONY: help install test lint format clean docker-build docker-run docker-stop dev-setup users

# Default target
help:
	@echo "Meshtopo Gateway Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install dependencies"
	@echo "  dev-setup    Setup development environment"
	@echo "  test         Run all tests"
	@echo "  test-password Run password utility tests"
	@echo "  test-user-manager Run user manager tests"
	@echo "  test-flask-app Run Flask app tests"
	@echo "  test-auth    Run authentication tests"
	@echo "  test-users   Run user management tests"
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
	@echo "  web-ui       Run the web UI"
	@echo "  config       Show configuration help"
	@echo ""
	@echo "User Management:"
	@echo "  users        Interactive user management"
	@echo "  hash-password Generate password hash"

# Install dependencies
install:
	pip3 install -r requirements.txt
	pip3 install -r requirements-web.txt

# Setup development environment
dev-setup: install
	pip3 install -r requirements.txt
	pip3 install -r requirements-web.txt
	pip3 install black flake8 mypy pytest pytest-cov isort pre-commit
	pre-commit install
	@echo "Development environment setup complete!"

# Run tests
test:
	python3 src/test_gateway.py
	python3 -c "from src.web_ui.utils.password import hash_password, verify_password; print('Password utilities test passed')"
	python3 tests/run_tests.py

# Run specific test modules
test-password:
	python3 tests/test_password_utils.py

test-user-manager:
	python3 tests/test_user_manager.py

test-flask-app:
	python3 tests/test_flask_app.py

test-auth:
	python3 tests/test_authentication.py

test-users:
	python3 tests/test_user_management.py

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
	docker build -t meshtopo-web:latest -f deploy/Dockerfile.web .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker containers
docker-stop:
	docker-compose down

# Run the gateway service
run:
	python3 src/gateway.py

# Run the web UI
web-ui:
	python3 src/web_ui/app.py

# Interactive user management
users:
	python3 scripts/user_manager.py interactive

# Generate password hash
hash-password:
	python3 src/web_ui/utils/password.py

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
	@echo "   - User accounts (see docs/authentication.md)"
	@echo ""
	@echo "3. Run the service:"
	@echo "   make run          # Core gateway only"
	@echo "   make web-ui       # Web UI only"
	@echo "   make docker-run   # Full stack with Docker"
	@echo ""
	@echo "4. Manage users:"
	@echo "   make users        # Interactive user management"
	@echo "   make hash-password # Generate password hash"
