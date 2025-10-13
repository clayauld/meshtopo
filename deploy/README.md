# Meshtopo Docker Deployment

<p align="center">
  <img src="../assets/images/Meshtopo-logo.png" alt="Meshtopo Logo" width="150">
</p>

This directory contains Docker Compose configurations for deploying Meshtopo using pre-built container images from GitHub Container Registry.

## Available Configurations

### Full Configuration (`docker-compose.yml`)

Complete Meshtopo deployment with all features:

- Core gateway service
- Integrated MQTT broker (Mosquitto)
- SSL/TLS termination with Traefik

### Minimal Configuration (`docker-compose-minimal.yaml`)

Minimal deployment with core functionality only:

- Core gateway service
- External MQTT broker connection
- No SSL or integrated MQTT broker

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
    docker-compose --profile core --profile mqtt up -d
    ```

    **Minimal deployment:**

    ```bash
    cd deploy
    docker-compose -f docker-compose-minimal.yaml up -d
    ```

## Container Images

The deployment uses pre-built images from GitHub Container Registry:

- **Gateway Service:** `ghcr.io/your-username/meshtopo:latest`

### Image Tags Available

- `latest` - Latest stable release
- `main` - Latest from main branch
- `develop` - Latest from develop branch
- `{commit-sha}` - Specific commit builds

## Configuration Files

- `config/config.yaml` - Full configuration (for docker-compose.yml)
- `config/config.yaml.minimal` - Minimal configuration (for docker-compose-minimal.yaml)

**Note:** Make sure to copy the appropriate configuration template and update it with your specific settings before deployment.

## Environment Variables

| Variable             | Description                    | Default             |
| -------------------- | ------------------------------ | ------------------- |
| `GITHUB_REPOSITORY`  | GitHub repository (owner/repo) | `clayauld/meshtopo` |
| `SSL_EMAIL`          | Email for SSL certificate      | Required for SSL    |
| `SSL_DOMAIN`         | Domain for SSL certificate     | Required for SSL    |
| `DNS_PROVIDER`       | DNS provider for challenge     | Optional            |
| `DNS_EMAIL`          | DNS provider email             | Required for DNS    |
| `DNS_API_TOKEN`      | DNS provider API token         | Required for DNS    |
| `DNS_ZONE_API_TOKEN` | DNS provider zone API token    | Optional for DNS    |

**SSL Challenge Methods:**

- **HTTP Challenge** (default): Requires port 80 open, works with any domain
- **DNS Challenge** (optional): No port 80 needed, requires DNS provider credentials

## Profiles (Full Configuration Only)

- `core` - Core gateway service
- `mqtt` - Integrated MQTT broker
- `ssl` - SSL/TLS termination

## SSL Configuration

When using the `ssl` profile, Traefik provides:

- **Traefik Dashboard**: `https://traefik.yourdomain.com` (port 8080)
- **MQTT WebSocket**: `wss://mqtt.yourdomain.com` (secure WebSocket connection)
- **Automatic SSL**: Let's Encrypt certificates with HTTP or DNS challenge
- **HTTP Redirect**: Automatic redirect from HTTP to HTTPS

**Requirements for SSL:**

- Domain name pointing to your server
- Ports 80 and 443 open
- Valid `SSL_EMAIL` and `SSL_DOMAIN` in `.env` file

## DNS Challenge Setup (Cloudflare)

For DNS challenge with Cloudflare:

1. **Get Cloudflare API Token:**

    - Go to Cloudflare Dashboard → My Profile → API Tokens
    - Create token with "Zone:Edit" permissions for your domain
    - Copy the token

2. **Configure Environment Variables:**

    ```bash
    # In deploy/.env
    DNS_PROVIDER=cloudflare
    DNS_EMAIL=your-email@example.com
    DNS_API_TOKEN=your_cloudflare_api_token
    ```

3. **Deploy with DNS Challenge:**

    ```bash
    docker-compose --profile core --profile mqtt --profile ssl up -d
    ```

**Benefits of DNS Challenge:**

- No need to expose port 80
- Works behind firewalls
- Supports wildcard certificates
- More secure for internal networks

## Multi-Architecture Support

Container images are built for both AMD64 and ARM64 architectures, making them compatible with:

- Intel/AMD x86_64 systems
- ARM64 systems (Apple Silicon, ARM-based servers)

## Security

- Images run as non-root user (`meshtopo`)
- Minimal base images (python:3.9-slim)
- Regular security updates through GitHub Actions
- Resource limits configured for production use

## Monitoring

Both configurations include:

- Health checks for service monitoring
- Structured logging with rotation
- Resource usage limits
- Automatic restart policies
