# Meshtopo Docker Deployment

This directory contains Docker Compose configurations for deploying Meshtopo using pre-built container images from GitHub Container Registry.

## Available Configurations

### Full Configuration (`docker-compose.yml`)

Complete Meshtopo deployment with all features:

-   Core gateway service
-   Web management interface
-   Integrated MQTT broker (Mosquitto)
-   SSL/TLS termination with Traefik
-   User management and authentication

### Minimal Configuration (`docker-compose-minimal.yaml`)

Minimal deployment with core functionality only:

-   Core gateway service
-   External MQTT broker connection
-   No web UI, SSL, or integrated MQTT broker

## Quick Start

1. **Copy environment configuration:**

    ```bash
    cp deploy/env.example deploy/.env
    ```

2. **Update configuration:**
   Edit `deploy/.env` and set your GitHub repository:

    ```bash
    GITHUB_REPOSITORY=your-username/meshtopo
    ```

3. **Choose your deployment:**

    **Full deployment:**

    ```bash
    cd deploy
    docker-compose --profile core --profile web --profile mqtt up -d
    ```

    **Minimal deployment:**

    ```bash
    cd deploy
    docker-compose -f docker-compose-minimal.yaml up -d
    ```

## Container Images

The deployment uses pre-built images from GitHub Container Registry:

-   **Gateway Service:** `ghcr.io/your-username/meshtopo:latest`
-   **Web UI:** `ghcr.io/your-username/meshtopo-web:latest`

### Image Tags Available

-   `latest` - Latest stable release
-   `main` - Latest from main branch
-   `develop` - Latest from develop branch
-   `{commit-sha}` - Specific commit builds

## Configuration Files

-   `config/config.yaml` - Full configuration (for docker-compose.yml)
-   `config/config.yaml.minimal` - Minimal configuration (for docker-compose-minimal.yaml)

## Environment Variables

| Variable            | Description                    | Default             |
| ------------------- | ------------------------------ | ------------------- |
| `GITHUB_REPOSITORY` | GitHub repository (owner/repo) | `clayauld/meshtopo` |
| `SSL_EMAIL`         | Email for SSL certificate      | Required for SSL    |
| `SSL_DOMAIN`        | Domain for SSL certificate     | Required for SSL    |

## Profiles (Full Configuration Only)

-   `core` - Core gateway service
-   `web` - Web management interface
-   `mqtt` - Integrated MQTT broker
-   `ssl` - SSL/TLS termination

## Multi-Architecture Support

Container images are built for both AMD64 and ARM64 architectures, making them compatible with:

-   Intel/AMD x86_64 systems
-   ARM64 systems (Apple Silicon, ARM-based servers)

## Security

-   Images run as non-root user (`meshtopo`)
-   Minimal base images (python:3.9-slim)
-   Regular security updates through GitHub Actions
-   Resource limits configured for production use

## Monitoring

Both configurations include:

-   Health checks for service monitoring
-   Structured logging with rotation
-   Resource usage limits
-   Automatic restart policies
