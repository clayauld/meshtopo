# Meshtopo - Meshtastic to CalTopo Gateway

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks with CalTopo mapping platforms, enabling real-time position tracking of field assets on high-quality maps.

## Overview

**Meshtopo** solves the communication gap between off-grid LoRa mesh networks (Meshtastic) and online mapping platforms (CalTopo). It acts as a reliable bridge that forwards location data from Meshtastic nodes directly to CalTopo maps, providing real-time situational awareness for backcountry coordinators, event organizers, and response teams.

## Features

-   **Real-time Position Forwarding**: Automatically forwards Meshtastic position packets to CalTopo
-   **Intelligent Node Mapping**: Automatically maps Meshtastic numeric node IDs to hardware IDs using fallback mechanisms, then to CalTopo device IDs
-   **Robust Error Handling**: Graceful handling of network issues and API failures
-   **Docker Deployment**: Easy deployment with Docker and Docker Compose
-   **Comprehensive Logging**: Detailed logging for monitoring and debugging
-   **Lightweight Design**: Minimal resource footprint for edge deployment

## Architecture

The system follows a simple linear data flow:

1. **Meshtastic Network** → LoRa mesh nodes with MQTT gateway
2. **MQTT Broker** → Central message broker (e.g., Mosquitto)
3. **Gateway Service** → This Python service (filters, transforms, forwards)
4. **CalTopo API** → Cloud mapping platform

## Quick Start

### Prerequisites

-   Python 3.9+ or Docker
-   Access to an MQTT broker with Meshtastic data
-   CalTopo account with API access

### Docker Deployment (Recommended)

1. **Clone and configure**:

    ```bash
    git clone https://github.com/clayauld/meshtopo.git
    cd meshtopo
    cp config/config.yaml.example config/config.yaml
    # Edit config/config.yaml with your settings
    ```

2. **Start the service**:

    ```bash
    docker-compose up -d
    ```

3. **View logs**:

    ```bash
    docker-compose logs -f
    ```

### Manual Installation

1. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2. **Configure the service**:

    ```bash
    cp config/config.yaml.example config/config.yaml
    # Edit config/config.yaml with your MQTT and CalTopo settings
    ```

3. **Run the gateway**:

    ```bash
    python src/gateway.py
    ```

## Configuration

The service is configured via `config/config.yaml`:

```yaml
# MQTT Broker Configuration
mqtt:
    broker: "192.168.1.100"
    port: 1883
    username: "your_mqtt_user"
    password: "your_mqtt_password"
    topic: "msh/REGION/2/json/+/+"

**Note**: Replace `REGION` with your LoRa region code. See [Meshtastic LoRa Region by Country](https://meshtastic.org/docs/configuration/region-by-country/) for the correct region code for your country.

# CalTopo API Configuration
caltopo:
    group: "MESH-TEAM-ALPHA"

# Node ID Mapping
nodes:
    "!823a4edc":
        device_id: "TEAM-LEAD"
    "!a4b8c2f0":
        device_id: "COMMS"
```

### Node Mapping Mechanism

Meshtopo uses an intelligent two-tier mapping system to handle different Meshtastic message types:

#### 1. Primary Mapping (Nodeinfo Messages)

When `nodeinfo` messages are received, the gateway builds a mapping from numeric node IDs to hardware IDs:

```json
{
    "from": 862485920,
    "type": "nodeinfo",
    "payload": {
        "id": "!33687da0",
        "longname": "AMRG3-Heltec"
    }
}
```

This creates: `862485920` → `!33687da0`

#### 2. Fallback Mapping (Position Messages)

When position messages arrive before nodeinfo messages, the gateway uses the `sender` field as a fallback:

```json
{
    "from": 862485920,
    "sender": "!33687da0",
    "type": "position",
    "payload": {
        "latitude_i": 612188460,
        "longitude_i": -1499001320
    }
}
```

This automatically maps: `862485920` → `!33687da0`

#### 3. Configuration Mapping

The final step maps hardware IDs to CalTopo device names using your configuration:

```yaml
nodes:
    "!33687da0":
        device_id: "AMRG3"
```

**Complete mapping chain**: `862485920` → `!33687da0` → `AMRG3`

This ensures position updates are never missed, even when nodeinfo messages are delayed or unavailable.

### Configuration Parameters

-   **mqtt.broker**: IP address or hostname of your MQTT broker
-   **mqtt.port**: MQTT broker port (default: 1883)
-   **mqtt.username/password**: MQTT authentication credentials
-   **mqtt.topic**: MQTT topic pattern for Meshtastic position packets (replace `REGION` with your LoRa region code)
-   **caltopo.group**: Your CalTopo group identifier
-   **nodes**: Mapping of Meshtastic hardware IDs to CalTopo device IDs

### LoRa Region Codes

The `REGION` in the MQTT topic must be replaced with the appropriate LoRa region code for your country. Common region codes include:

-   **US** - United States
-   **EU_868** - European Union (868 MHz)
-   **ANZ** - Australia/New Zealand
-   **CN** - China
-   **JP** - Japan
-   **KR** - Korea
-   **IN** - India
-   **BR_902** - Brazil
-   **RU** - Russia

For the complete list of region codes by country, see the [Meshtastic LoRa Region by Country documentation](https://meshtastic.org/docs/configuration/region-by-country/).

## Data Flow

1. **Meshtastic nodes** broadcast position data via LoRa
2. **MQTT Gateway** forwards data to MQTT broker
3. **Gateway Service** subscribes to position topics
4. **Position packets** are parsed and validated
5. **CalTopo API** receives formatted position reports
6. **CalTopo maps** display real-time positions

## API Integration

### Meshtastic Input Format

The service processes JSON position packets from Meshtastic:

```json
{
    "from": "!823a4edc",
    "type": "position",
    "payload": {
        "latitude_i": 612188460,
        "longitude_i": -1499001320
    }
}
```

### CalTopo Output Format

Position data is forwarded to CalTopo via HTTP GET:

```
https://caltopo.com/api/v1/position/report/{GROUP}?id={DEVICE_ID}&lat={LAT}&lng={LNG}
```

## Error Handling

The service includes comprehensive error handling:

-   **MQTT Disconnection**: Automatic reconnection with exponential backoff
-   **Invalid JSON**: Malformed packets are logged and discarded
-   **Unmapped Nodes**: Unknown node IDs are logged at DEBUG level
-   **API Failures**: CalTopo API errors are logged with full details
-   **Network Issues**: Graceful handling of connectivity problems

## Logging

The service provides detailed logging at multiple levels:

-   **INFO**: Successful operations and status updates
-   **WARN**: Recoverable errors and reconnection attempts
-   **ERROR**: API failures and critical errors
-   **DEBUG**: Detailed debugging information

## Development

### Project Structure

```
meshtopo/
├── config/             # Configuration files
│   ├── config.py       # Configuration management
│   └── config.yaml.example # Configuration template
├── deploy/             # Deployment files
│   ├── Dockerfile      # Container definition
│   ├── docker-compose.yml # Docker Compose configuration
│   └── meshtopo.service # Systemd service file
├── docs/               # Documentation
│   └── design.md       # Design documentation
├── scripts/            # Shell scripts
│   └── install.sh      # Installation script
├── src/                # Python source code
│   ├── gateway.py      # Main application entry point
│   ├── gateway_app.py  # Main application class
│   ├── mqtt_client.py  # MQTT communication
│   ├── caltopo_reporter.py # CalTopo API integration
│   └── test_gateway.py # Test suite
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project configuration
├── Makefile           # Development commands
└── README.md          # This file
```

### Running Tests

```bash
python src/test_gateway.py
```

### Code Style

The project follows PEP 8 guidelines with automatic formatting via `black`:

```bash
black .
```

## Deployment

### Docker

The service is designed for containerized deployment:

```bash
# Build image
docker build -t meshtopo .

# Run container
docker run -d --name meshtopo -v ./config/config.yaml:/app/config/config.yaml meshtopo
```

### Docker Compose

For production deployment:

```bash
docker-compose up -d
```

### Systemd Service

For system-level deployment:

```bash
sudo cp deploy/meshtopo.service /etc/systemd/system/
sudo systemctl enable meshtopo
sudo systemctl start meshtopo
```

## Monitoring

### Health Checks

The service provides several monitoring endpoints:

-   **Log monitoring**: `docker-compose logs -f`
-   **Process status**: `docker-compose ps`
-   **Resource usage**: `docker stats meshtopo`

### Metrics

Key metrics to monitor:

-   MQTT connection status
-   Position packets processed per minute
-   CalTopo API success rate
-   Error rates by type
-   Memory and CPU usage

## Troubleshooting

### Common Issues

1. **MQTT Connection Failed**

    - Verify broker address and credentials
    - Check network connectivity
    - Ensure MQTT broker is running

2. **No Position Updates**

    - Verify Meshtastic MQTT gateway is configured
    - Check topic pattern in configuration
    - Ensure nodes are broadcasting position data

3. **CalTopo API Errors**
    - Verify group ID and device mappings
    - Check CalTopo API status
    - Verify internet connectivity

### Debug Mode

Enable debug logging:

```yaml
logging:
    level: DEBUG
```

## License

This project is licensed under the GNU Affero General Public License v3 (AGPLv3). See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:

-   Create an issue on GitHub
-   Check the troubleshooting section
-   Review the configuration examples

## Future Enhancements

-   Two-way messaging from CalTopo to Meshtastic
-   Additional telemetry forwarding (battery, signal strength)
-   Web-based status dashboard
-   Multiple CalTopo group support
-   Position history and analytics
