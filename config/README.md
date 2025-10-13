# Meshtopo Configuration

<p align="center">
  <img src="../assets/images/Meshtopo-logo.png" alt="Meshtopo Logo" width="150">
</p>

This directory contains configuration files and examples for the Meshtopo gateway service.

## Configuration Files

### Main Configuration

- **`config.yaml`** - Your active configuration file (not tracked in git)
- **`config.yaml.example`** - Complete example with all options documented
- **`config.yaml.basic`** - Minimal configuration for basic setup
- **`config.yaml.minimal`** - Bare minimum configuration for testing
- **`config.yaml.production`** - Production-ready configuration
- **`config.yaml.docker`** - Docker-optimized configuration

## Quick Setup

1. **Copy an example configuration**:

    ```bash
    cp config.yaml.example config.yaml
    ```

2. **Edit the configuration**:

    ```bash
    nano config.yaml
    ```

3. **Required settings**:
    - MQTT broker connection details
    - CalTopo Team Account connect key
    - MQTT topic pattern with correct region code

## Configuration Structure

### MQTT Configuration

```yaml
mqtt:
    broker: "192.168.1.100" # MQTT broker hostname/IP
    port: 1883 # MQTT broker port
    username: "user" # MQTT username
    password: "pass" # MQTT password
    topic: "msh/US/2/json/+/+" # MQTT topic pattern
```

### CalTopo Configuration

```yaml
caltopo:
    connect_key: "YOUR_CONNECT_KEY_HERE" # From Team Account access URL
    api_mode: "connect_key" # API mode: "connect_key" or "group"
    group: "SARTEAM" # Global GROUP (required if api_mode is "group")
```

**API Mode Options:**

- **connect_key** (default): Uses CalTopo Team Account connect key
- **group**: Uses GROUP-based custom integration with optional per-device GROUP overrides

### Optional Node Overrides

```yaml
nodes:
    "!823a4edc": # Meshtastic hardware ID
        device_id: "TEAM-LEAD" # Custom display name in CalTopo
        group: "LEADERSHIP" # Optional per-device GROUP override
```

### Device Management Configuration

```yaml
devices:
    allow_unknown_devices: true # Allow unknown devices to send position updates
```

**Device Access Control:**

- **true** (default): Unknown devices are tracked and can send position updates
- **false**: Unknown devices are tracked but position updates are blocked

### Internal MQTT Broker Configuration

```yaml
mqtt_broker:
    enabled: true # Enable internal Mosquitto broker
    port: 1883 # MQTT broker port
    websocket_port: 9001 # WebSocket port for web clients
    persistence: true # Enable message persistence
    max_connections: 1000 # Maximum concurrent connections
    allow_anonymous: false # Allow anonymous connections
    users:
        - username: "meshtopo" # MQTT username
          password: "secure_password" # MQTT password
          acl: "readwrite" # Access level: read, write, readwrite
        - username: "readonly" # Read-only user
          password: "readonly_pass" # Read-only password
          acl: "read" # Read-only access
    acl_enabled: false # Enable Access Control Lists
```

## Obtaining CalTopo Connect Key

1. Log into your CalTopo Team Account
2. Navigate to **Team Settings** → **Access URLs**
3. Copy the connect key from your team's access URL
4. The connect key looks like: `G3rvYRwG3TtrQVyUIB3WKfbyzFqSfUldGDxC4blVzrkte`

## Region Codes

Replace `US` in the MQTT topic with your LoRa region code:

- **US** - United States
- **EU_868** - European Union (868 MHz)
- **ANZ** - Australia/New Zealand
- **CN** - China
- **JP** - Japan
- **KR** - Korea
- **IN** - India
- **BR_902** - Brazil
- **RU** - Russia

For the complete list, see [Meshtastic LoRa Region by Country](https://meshtastic.org/docs/configuration/region-by-country/).

## Device Registration

Devices automatically register in CalTopo using their Meshtastic callsigns:

1. **Automatic**: Devices appear when they first report position
2. **Callsign**: Uses Meshtastic `longname` field as identifier
3. **Override**: Optional custom display names in `nodes` section
4. **No Setup**: No pre-registration required

## Internal MQTT Broker Setup

### Broker Quick Setup

1. **Enable broker in config.yaml**:

    ```yaml
    mqtt_broker:
        enabled: true
        users:
            - username: "meshtopo"
              password: "your_password"
              acl: "readwrite"
    ```

2. **Generate configuration**:

    ```bash
    make setup-broker
    ```

3. **Start broker**:

    ```bash
    docker-compose up -d mosquitto
    ```

### User Management

- **Username/Password**: Define MQTT users in `mqtt_broker.users`
- **ACL Levels**: `read`, `write`, or `readwrite`
- **Password Security**: Passwords are hashed using Mosquitto's PBKDF2 method
- **Anonymous Access**: Disabled by default for security

### Security Features

- **No Anonymous Access**: All connections require authentication
- **Password Hashing**: Uses PBKDF2 with SHA512
- **ACL Support**: Fine-grained access control (optional)
- **Connection Limits**: Configurable max connections
- **WebSocket Support**: Secure WebSocket connections on separate port

## Logging Configuration

```yaml
logging:
    level: "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
    file:
        enabled: true # Enable file logging
        path: "/var/log/meshtopo/meshtopo.log"
        max_size: "10MB" # Maximum log file size
        backup_count: 5 # Number of backup files
```

## Environment-Specific Configurations

### Development

- Use `config.yaml.minimal` for testing
- Set logging level to `DEBUG`
- Use local MQTT broker

### Production

- Use `config.yaml.production` as template
- Set logging level to `WARNING`
- Configure proper log rotation
- Use secure MQTT credentials

### Docker

- Use `config.yaml.docker` as template
- Set MQTT broker to service name (e.g., `mosquitto`)
- Configure log paths for container

## Troubleshooting

### Configuration Validation

```bash
python -c "from config.config import Config; Config.from_file('config.yaml')"
```

### Common Issues

1. **Invalid connect key**: Ensure it's from Team Account access URL
2. **Wrong region code**: Check Meshtastic documentation for your country
3. **MQTT connection failed**: Verify broker settings and network connectivity
4. **Devices not appearing**: Check that nodes are sending position data

## Security Notes

- Never commit `config.yaml` to version control (contains sensitive data)
- Use strong MQTT passwords
- Keep CalTopo connect key secure
- Consider using environment variables for sensitive data in production
