# Meshtopo - Meshtastic to CalTopo Gateway

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks with CalTopo mapping platforms, enabling real-time position tracking of field assets on high-quality maps.

## Overview

**Meshtopo** solves the communication gap between off-grid LoRa mesh networks (Meshtastic) and online mapping platforms (CalTopo). It acts as a reliable bridge that forwards location data from Meshtastic nodes directly to CalTopo maps, providing real-time situational awareness for backcountry coordinators, event organizers, and response teams.

## Features

- **Real-time Position Forwarding**: Automatically forwards Meshtastic position packets to CalTopo
- **Configurable Node Mapping**: Maps Meshtastic hardware IDs to CalTopo device IDs
- **Robust Error Handling**: Graceful handling of network issues and API failures
- **Docker Deployment**: Easy deployment with Docker and Docker Compose
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Lightweight Design**: Minimal resource footprint for edge deployment

## Architecture

The system follows a simple linear data flow:

1. **Meshtastic Network** → LoRa mesh nodes with MQTT gateway
2. **MQTT Broker** → Central message broker (e.g., Mosquitto)
3. **Gateway Service** → This Python service (filters, transforms, forwards)
4. **CalTopo API** → Cloud mapping platform

## Quick Start

### Prerequisites

- Python 3.9+ or Docker
- Access to an MQTT broker with Meshtastic data
- CalTopo account with API access

### Docker Deployment (Recommended)

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd meshtopo
   cp config.yaml.example config.yaml
   # Edit config.yaml with your settings
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
   cp config.yaml.example config.yaml
   # Edit config.yaml with your MQTT and CalTopo settings
   ```

3. **Run the gateway**:
   ```bash
   python gateway.py
   ```

## Configuration

The service is configured via `config.yaml`:

```yaml
# MQTT Broker Configuration
mqtt:
  broker: "192.168.1.100"
  port: 1883
  username: "your_mqtt_user"
  password: "your_mqtt_password"
  topic: "msh/+/+/json/position/#"

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

### Configuration Parameters

- **mqtt.broker**: IP address or hostname of your MQTT broker
- **mqtt.port**: MQTT broker port (default: 1883)
- **mqtt.username/password**: MQTT authentication credentials
- **mqtt.topic**: MQTT topic pattern for Meshtastic position packets
- **caltopo.group**: Your CalTopo group identifier
- **nodes**: Mapping of Meshtastic hardware IDs to CalTopo device IDs

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
  "fromId": "!823a4edc",
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

- **MQTT Disconnection**: Automatic reconnection with exponential backoff
- **Invalid JSON**: Malformed packets are logged and discarded
- **Unmapped Nodes**: Unknown node IDs are logged at DEBUG level
- **API Failures**: CalTopo API errors are logged with full details
- **Network Issues**: Graceful handling of connectivity problems

## Logging

The service provides detailed logging at multiple levels:

- **INFO**: Successful operations and status updates
- **WARN**: Recoverable errors and reconnection attempts
- **ERROR**: API failures and critical errors
- **DEBUG**: Detailed debugging information

## Development

### Project Structure

```
meshtopo/
├── gateway.py          # Main application entry point
├── config.py           # Configuration management
├── mqtt_client.py      # MQTT communication
├── caltopo_reporter.py # CalTopo API integration
├── requirements.txt    # Python dependencies
├── config.yaml.example # Configuration template
├── Dockerfile          # Container definition
├── docker-compose.yml  # Docker Compose configuration
└── README.md          # This file
```

### Running Tests

```bash
python -m pytest tests/
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
docker run -d --name meshtopo -v ./config.yaml:/app/config.yaml meshtopo
```

### Docker Compose

For production deployment:

```bash
docker-compose up -d
```

### Systemd Service

For system-level deployment:

```bash
sudo cp meshtopo.service /etc/systemd/system/
sudo systemctl enable meshtopo
sudo systemctl start meshtopo
```

## Monitoring

### Health Checks

The service provides several monitoring endpoints:

- **Log monitoring**: `docker-compose logs -f`
- **Process status**: `docker-compose ps`
- **Resource usage**: `docker stats meshtopo`

### Metrics

Key metrics to monitor:

- MQTT connection status
- Position packets processed per minute
- CalTopo API success rate
- Error rates by type
- Memory and CPU usage

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

- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration examples

## Future Enhancements

- Two-way messaging from CalTopo to Meshtastic
- Additional telemetry forwarding (battery, signal strength)
- Web-based status dashboard
- Multiple CalTopo group support
- Position history and analytics