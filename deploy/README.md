# Docker Deployment Guide

This directory contains Docker Compose configurations for deploying the Meshtopo Gateway Service.

## Quick Start

1. **Set up environment:**

   ```bash
   make docker-setup
   ```

2. **Edit configuration:**

   ```bash
   nano deploy/.env
   ```

3. **Start services:**

   ```bash
   make docker-run
   ```

## Configuration

### Environment Variables

The deployment uses environment variables to control configuration. Copy `.env.example` to `.env` and customize:

```bash
cp deploy/.env.example deploy/.env
```

#### Required Variables

- `SSL_DOMAIN`: Your domain name for SSL certificates
- `SSL_EMAIL`: Email for Let's Encrypt certificates

#### Optional Variables

- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_WS_PORT`: MQTT WebSocket port (default: 9001)
- `MQTT_AUTH_ENABLED`: Enable MQTT authentication (default: false)
- `MQTT_ACL_ENABLED`: Enable MQTT ACL (default: false)

### Profiles

Docker Compose uses profiles to control which services start:

- `core`: Meshtopo gateway service
- `mqtt`: MQTT broker service
- `ssl`: Traefik reverse proxy with SSL

## Deployment Options

### Minimal Deployment

```bash
make docker-run-minimal
```

Runs only the core gateway service without MQTT broker.

### Full Stack with MQTT

```bash
make docker-run
```

Runs core gateway + MQTT broker.

### Full Stack with SSL

```bash
SSL_DOMAIN=yourdomain.com make docker-run-ssl
```

Runs all services with SSL/TLS termination.

## MQTT Broker Configuration

The MQTT broker configuration is managed through environment variables and the `generate_mosquitto_config.py` script:

1. **Configure in config.yaml:**

   ```yaml
   mqtt:
     broker:
       enabled: true
       port: 1883
       websocket_port: 9001
       allow_anonymous: false
       users:
         - username: "user1"
           password: "password1"
       acl_enabled: true
   ```

2. **Generate configuration:**

   ```bash
   make generate-broker-config
   ```

3. **Start with MQTT:**

   ```bash
   make docker-run
   ```

## Troubleshooting

### Check service status

```bash
make docker-status
```

### View logs

```bash
make docker-logs
```

### Clean up

```bash
make docker-clean
```

## Migration from Override Files

If you were previously using `docker-compose.override.yml` files:

1. The system now uses environment variables instead
2. Run `make docker-setup` to create a `.env` file
3. Configure your MQTT settings in the `.env` file
4. Use the standard `make docker-run` command

This approach is more maintainable and follows Docker Compose best practices.
