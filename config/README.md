# Meshtopo Configuration Examples

This directory contains several configuration examples for different deployment scenarios.

## Configuration Files

### `config.yaml.example`

**Comprehensive example** with all features enabled and documented. This is the most complete configuration showing:

-   Full MQTT broker configuration with SSL
-   Complete CalTopo Team API integration
-   Multiple users with different roles and CalTopo credentials
-   Multiple Meshtastic nodes with descriptions
-   Advanced logging configuration
-   Complete web UI settings with security features
-   SSL/TLS configuration
-   Optional integrated MQTT broker
-   Advanced performance and filtering settings
-   Environment-specific overrides

### `config.yaml.minimal`

**Absolute minimal configuration** for core functionality only:

-   External MQTT broker connection
-   CalTopo position reporting
-   Meshtastic node mapping
-   Basic console logging
-   All advanced features disabled (no Web UI, SSL, users, etc.)

### `config.yaml.basic`

**Minimal configuration** for getting started quickly. Perfect for:

-   Development and testing
-   Simple single-user setups
-   Local deployments
-   Learning the system

### `config.yaml.production`

**Production-ready configuration** with security best practices:

-   Strong authentication and security settings
-   Optimized logging for production
-   Stricter rate limiting
-   SSL/TLS with Let's Encrypt
-   Performance optimizations
-   Security headers and policies

### `config.yaml.docker`

**Docker Compose optimized** configuration for containerized deployments:

-   Docker service names and internal ports
-   Traefik SSL termination
-   Integrated Mosquitto broker
-   Docker-specific paths and settings
-   Health checks and resource limits
-   Traefik labels for automatic SSL

## Quick Start

1. **Choose the appropriate example** for your use case:
    - `config.yaml.minimal` - Core functionality only (no Web UI)
    - `config.yaml.basic` - Simple setup with Web UI
    - `config.yaml.production` - Full production deployment
    - `config.yaml.docker` - Docker Compose deployment
2. **Copy it to `config.yaml`**:
    ```bash
    cp config/config.yaml.minimal config/config.yaml  # For minimal setup
    cp config/config.yaml.basic config/config.yaml    # For basic setup
    ```
3. **Edit the configuration** with your specific settings:
    - MQTT broker details
    - CalTopo group ID
    - Meshtastic node mappings
    - User accounts and passwords (if using Web UI)
4. **Generate password hashes** (if using Web UI):
    ```bash
    python3 src/web_ui/utils/password.py 'your_password'
    ```
5. **Start the service**:
    ```bash
    python3 src/gateway.py          # Core service only (minimal config)
    python3 src/web_ui/app.py       # Web UI only (basic+ configs)
    # or
    docker-compose up -d            # Full stack with Docker
    ```

## Minimal Configuration (Core Functionality Only)

The `config.yaml.minimal` file provides the absolute minimum configuration needed for core Meshtopo functionality:

### What's Included (Core Features)

-   **MQTT Client**: Connects to external MQTT broker to receive Meshtastic messages
-   **CalTopo Integration**: Forwards position data to CalTopo mapping platform
-   **Node Mapping**: Maps Meshtastic hardware IDs to CalTopo device names
-   **Basic Logging**: Console logging for monitoring and debugging

### What's Disabled (Advanced Features)

-   **Web UI**: No web interface for configuration or monitoring
-   **User Management**: No authentication or user accounts
-   **SSL/TLS**: No encryption (use external SSL termination if needed)
-   **Team API**: No CalTopo Team API features (map selection, etc.)
-   **File Logging**: No log files (console only)
-   **Integrated MQTT Broker**: Uses external MQTT broker only

### Use Cases for Minimal Configuration

-   **Embedded Systems**: Resource-constrained environments
-   **Headless Servers**: No GUI or web interface needed
-   **Simple Deployments**: Just need position forwarding
-   **Development**: Testing core functionality without complexity
-   **Legacy Integration**: Existing systems that don't need advanced features

### Running with Minimal Configuration

```bash
# Copy minimal config
cp config/config.yaml.minimal config/config.yaml

# Edit with your settings
nano config/config.yaml

# Run core gateway only
python3 src/gateway.py
```

### Minimal Configuration Requirements

-   External MQTT broker (Mosquitto, AWS IoT, etc.)
-   CalTopo group ID
-   At least one Meshtastic node mapping
-   Python 3.9+ with basic dependencies

## Configuration Sections

### MQTT Configuration

```yaml
mqtt:
    broker: "your-mqtt-broker.com"
    port: 1883
    username: "your_username"
    password: "your_password"
    topic: "msh/REGION/2/json/+/+"

**Region Codes**: Replace `REGION` with the appropriate LoRa region code for your country. Common region codes:
- `US` - United States
- `EU_868` - European Union (868 MHz)
- `ANZ` - Australia/New Zealand
- `CN` - China
- `JP` - Japan

See the [Meshtastic LoRa Region by Country documentation](https://meshtastic.org/docs/configuration/region-by-country/) for the complete list of region codes.
```

### CalTopo Configuration

```yaml
caltopo:
    group: "YOUR-GROUP-ID"
    map_id: "" # Set via web UI
    team_api:
        enabled: true
        credential_id: "YOUR_CREDENTIAL_ID"
        secret_key: "YOUR_SECRET_KEY"
```

### User Management

```yaml
users:
    - username: "admin"
      password_hash: "$2b$12$..." # Generate with password utility
      role: "admin"
      caltopo_credentials:
          credential_id: "ADMIN_CRED"
          secret_key: "ADMIN_SECRET"
          accessible_maps: ["map1", "map2"]
```

### Node Mapping

The gateway uses an intelligent mapping system to handle Meshtastic messages:

#### Automatic Node ID Discovery

The gateway automatically builds mappings between numeric node IDs and hardware IDs using two methods:

1. **Primary Method (Nodeinfo Messages)**: When `nodeinfo` messages are received, the gateway extracts the hardware ID from the payload
2. **Fallback Method (Position Messages)**: When position messages arrive first, the gateway uses the `sender` field as a fallback

#### Configuration Mapping

You only need to configure the final mapping from hardware IDs to CalTopo device names:

```yaml
nodes:
    "!12345678": # Meshtastic hardware ID
        device_id: "MY-DEVICE" # CalTopo device name
        description: "Device description"
        enabled: true
```

#### Complete Mapping Chain

The gateway creates this mapping chain automatically:

-   **Numeric Node ID** (from `from` field) → **Hardware ID** (from `sender` field or nodeinfo payload) → **CalTopo Device Name** (from configuration)

This ensures position updates are never missed, even when nodeinfo messages are delayed or unavailable.

## Security Best Practices

### Password Security

-   Use strong, unique passwords for each user
-   Generate password hashes using the provided utility
-   Never store plain text passwords in configuration files

### SSL/TLS Configuration

-   Always use SSL in production environments
-   Use Let's Encrypt for automatic certificate management
-   Enable secure cookies and HTTP-only flags

### Rate Limiting

-   Enable rate limiting for all production deployments
-   Set appropriate limits based on your usage patterns
-   Monitor for abuse and adjust limits as needed

### User Roles

-   Use admin role only for system administrators
-   Assign user role for regular operators
-   Limit CalTopo access based on operational needs

## Environment-Specific Settings

### Development

-   Use `127.0.0.1` for web UI host
-   Disable SSL for easier testing
-   Use DEBUG or INFO log levels
-   Enable access logging for debugging

### Production

-   Use `0.0.0.0` for web UI host
-   Enable SSL with proper certificates
-   Use WARNING or ERROR log levels
-   Implement proper backup strategies

### Docker

-   Use Docker service names for internal communication
-   Let Traefik handle SSL termination
-   Use Docker volumes for persistent data
-   Configure health checks and resource limits

## Troubleshooting

### Common Issues

**"Invalid username or password"**

-   Verify password hash was generated correctly
-   Check username spelling in configuration
-   Ensure user exists in users section

**"MQTT connection failed"**

-   Verify broker address and port
-   Check username/password credentials
-   Ensure network connectivity

**"CalTopo API error"**

-   Verify credential ID and secret key
-   Check CalTopo group ID
-   Ensure Team API is enabled if needed

**"Web UI not accessible"**

-   Check host and port settings
-   Verify SSL configuration
-   Check firewall rules

### Log Analysis

-   Check log files for error messages
-   Use appropriate log levels for your environment
-   Monitor access logs for security issues
-   Set up log rotation to manage disk space

## Support

For additional help:

-   Check the main README.md file
-   Review the authentication documentation
-   Examine the Docker Compose configuration
-   Test with the basic configuration first
