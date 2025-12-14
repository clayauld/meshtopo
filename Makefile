# Meshtopo Gateway Service - Development Makefile

# Determine repository name from GITHUB_REPOSITORY environment variable
REPO := $(if $(GITHUB_REPOSITORY),$(GITHUB_REPOSITORY),clayauld/meshtopo)

.PHONY: help setup install test lint format clean docker-setup docker-build docker-pull docker-run docker-run-minimal docker-run-ssl docker-stop docker-status docker-logs docker-clean docker-login docker-push docker-push-default dev-setup setup-broker generate-broker-config

# Default target
help:
	@echo "Meshtopo Gateway Service - Available Commands:"
	@echo ""
	@echo "Onboarding:"
	@echo "  setup                Run the interactive setup wizard"
	@echo ""
	@echo "Development:"
	@echo "  install              Install dependencies"
	@echo "  dev-setup            Setup development environment"
	@echo "  test                 Run tests (excludes slow integration tests)"
	@echo "  test-full            Run all tests including integration tests"
	@echo "  test-integration     Run integration tests"
	@echo "  test-config          Run configuration tests"
	@echo "  test-gateway         Run gateway tests"
	@echo "  test-mqtt            Run MQTT topic format tests"
	@echo "  lint                 Run linting checks"
	@echo "  format               Format code with black and isort"
	@echo "  clean                Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-setup        Set up Docker environment (.env file)"
	@echo "  docker-build        Build Docker images for ghcr.io"
	@echo "  docker-pull         Pull Docker images from ghcr.io"
	@echo "  docker-run          Run full stack with Docker Compose"
	@echo "  docker-run-minimal  Run minimal gateway only"
	@echo "  docker-run-ssl      Run with SSL/Traefik (requires SSL_DOMAIN)"
	@echo "  docker-stop         Stop Docker containers"
	@echo "  docker-status       Show container status"
	@echo "  docker-logs         Show container logs"
	@echo "  docker-clean        Clean up Docker resources"
	@echo "  docker-login        Login to GitHub Container Registry"
	@echo "  docker-push         Push images to ghcr.io (requires GITHUB_REPOSITORY)"
	@echo "  docker-push-default Push images with default repository name"
	@echo ""
	@echo "Service:"
	@echo "  run          Run the gateway service"
	@echo "  config       Show configuration help"
	@echo ""
	@echo "MQTT Broker:"
	@echo "  setup-broker Setup internal MQTT broker"
	@echo "  generate-broker-config Generate broker configuration files"

# Run the interactive setup wizard
setup:
	python3 scripts/setup_wizard.py

# Helper for virtual environment check
VENV_CHECK := @if [ -z "$${VIRTUAL_ENV}" ]; then \
	echo "Error: No Python virtual environment activated."; \
	echo "Please create and activate a virtual environment (e.g., 'python3 -m venv .venv && source .venv/bin/activate')."; \
	exit 1; \
fi

# Install dependencies
install:
	$(VENV_CHECK)
	pip3 install -r requirements.txt

# Setup development environment
dev-setup: install
	$(VENV_CHECK)
	pip3 install -r requirements-dev.txt
	python3 -m pre_commit install
	@echo "Development environment setup complete!"

# Run tests (excludes slow integration tests)
test:
	$(VENV_CHECK)
	python3 -m pytest -m "not integration" tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml

# Run all tests including integration tests
test-full:
	$(VENV_CHECK)
	python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml

# Run integration tests
test-integration:
	$(VENV_CHECK)
	python3 -m pytest tests/integration/ -v --tb=short
# Run specific test modules
test-config:
	$(VENV_CHECK)
	python3 -m pytest tests/test_config.py -v

test-gateway:
	$(VENV_CHECK)
	python3 -m pytest tests/test_gateway_app.py -v

test-mqtt:
	$(VENV_CHECK)
	python3 -m pytest tests/test_mqtt_topic_format.py -v

# Format and lint code using pre-commit
format:
	$(VENV_CHECK)
	pre-commit run --all-files
	@echo "Code formatting and linting complete!"

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

# Docker environment setup
docker-setup:
	@echo "Setting up Docker environment..."
	@if [ ! -f deploy/.env ]; then \
		cp deploy/.env.example deploy/.env; \
		echo "Created .env file from template. Please edit deploy/.env with your configuration."; \
	else \
		echo ".env file already exists. Skipping creation."; \
	fi
	@echo "Docker environment setup complete!"

# Build and push Docker images to GitHub Container Registry
docker-build:
	@echo "Building Docker image for ghcr.io..."
	@if [ -z "$(GITHUB_REPOSITORY)" ]; then \
		echo "Warning: GITHUB_REPOSITORY not set, using default: clayauld/meshtopo"; \
	fi; \
	docker build -t ghcr.io/$(REPO):latest -t ghcr.io/$(REPO):$(shell git rev-parse --short HEAD) -f deploy/Dockerfile .
	@echo "Docker images built successfully!"
	@echo "To push to registry, run: make docker-push"

# Pull Docker images from GitHub Container Registry
docker-pull:
	@echo "Pulling Docker image from ghcr.io..."
	@if [ -z "$(GITHUB_REPOSITORY)" ]; then \
		echo "Warning: GITHUB_REPOSITORY not set, using default: clayauld/meshtopo"; \
	fi; \
	docker pull ghcr.io/$(REPO):latest

# Run with Docker Compose (full stack)
docker-run:
	@echo "Starting Meshtopo services with Docker Compose..."
	@if [ ! -f deploy/.env ]; then \
		echo "Warning: No .env file found. Using defaults. Run 'make docker-setup' to configure."; \
	fi
	cd deploy && docker compose --profile core --profile mqtt up -d
	@echo "Services started! Check status with: make docker-status"

# Run with Docker Compose (minimal - gateway only)
docker-run-minimal:
	@echo "Starting Meshtopo gateway (minimal) with Docker Compose..."
	cd deploy && docker compose -f docker-compose-minimal.yaml up -d
	@echo "Minimal services started! Check status with: make docker-status"

# Run with Docker Compose (with SSL/Traefik)
docker-run-ssl:
	@echo "Starting Meshtopo services with SSL/Traefik..."
	@if [ -z "$(SSL_DOMAIN)" ]; then echo "Error: SSL_DOMAIN environment variable required"; exit 1; fi
	cd deploy && docker compose --profile core --profile mqtt --profile ssl up -d
	@echo "SSL services started! Check status with: make docker-status"

# Stop Docker containers
docker-stop:
	@echo "Stopping Meshtopo services..."
	cd deploy && docker compose down
	cd deploy && docker compose -f docker-compose-minimal.yaml down
	@echo "Services stopped!"

# Show Docker container status
docker-status:
	@echo "=== Docker Container Status ==="
	docker ps --filter "name=meshtopo" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "=== Docker Compose Services ==="
	cd deploy && docker compose ps

# Show Docker logs
docker-logs:
	@echo "Showing logs for Meshtopo services..."
	docker logs meshtopo-gateway --tail=50 -f

# Clean up Docker resources
docker-clean:
	@echo "Cleaning up Docker resources..."
	docker compose -f deploy/docker-compose.yml down -v --remove-orphans
	docker compose -f deploy/docker-compose-minimal.yaml down -v --remove-orphans
	docker system prune -f
	@echo "Docker cleanup complete!"

# Login to GitHub Container Registry
docker-login:
	@echo "Logging into GitHub Container Registry..."
	@echo "You need to set GITHUB_TOKEN environment variable"
	docker login ghcr.io -u $(GITHUB_ACTOR) -p $(GITHUB_TOKEN)

# Push Docker images to registry
docker-push:
	@echo "Pushing Docker images to ghcr.io..."
	@if [ -z "$(GITHUB_REPOSITORY)" ]; then \
		echo "Error: GITHUB_REPOSITORY environment variable required for pushing"; \
		echo ""; \
		echo "To push images, set the GITHUB_REPOSITORY environment variable:"; \
		echo "  export GITHUB_REPOSITORY=your-username/meshtopo"; \
		echo "  make docker-push"; \
		echo ""; \
		echo "Or push manually:"; \
		echo "  docker push ghcr.io/clayauld/meshtopo:latest"; \
		echo "  docker push ghcr.io/clayauld/meshtopo:$(shell git rev-parse --short HEAD)"; \
		exit 1; \
	fi; \
	docker push ghcr.io/$(GITHUB_REPOSITORY):latest; \
	docker push ghcr.io/$(GITHUB_REPOSITORY):$(shell git rev-parse --short HEAD)
	@echo "Images pushed successfully!"

# Push Docker images with default repository name
docker-push-default:
	@echo "Pushing Docker images to ghcr.io with default repository..."
	docker push ghcr.io/clayauld/meshtopo:latest
	docker push ghcr.io/clayauld/meshtopo:$(shell git rev-parse --short HEAD)
	@echo "Images pushed successfully!"

# Run the gateway service
run:
	$(VENV_CHECK)
	python3 src/gateway.py

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
	@echo "   make test-integration # Run integration tests"
	@echo ""
	@echo "4. Setup internal MQTT broker:"
	@echo "   make setup-broker # Setup and start internal broker"
	@echo "   make generate-broker-config # Generate broker config files only"
