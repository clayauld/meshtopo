# Meshtopo - Meshtastic to CalTopo Gateway

<p align="center">
  <img src="assets/images/Meshtopo-logo.png" alt="Meshtopo Logo" width="200">
</p>

A lightweight Python gateway service that bridges Meshtastic LoRa mesh networks with CalTopo mapping platforms, enabling real-time position tracking of field assets on high-quality maps.

---

## What is `meshtopo`?

**Meshtopo** solves the communication gap between off-grid LoRa mesh networks (Meshtastic) and online mapping platforms (CalTopo). It acts as a reliable bridge that forwards location data from Meshtastic nodes directly to CalTopo maps, providing real-time situational awareness for backcountry coordinators, event organizers, and response teams.

Key features include:

- **Real-time Position Forwarding**: Automatically forwards Meshtastic position packets to CalTopo.
- **Automatic Device Registration**: Devices automatically appear in CalTopo using their callsigns.
- **Docker Deployment**: Easy deployment with Docker and Docker Compose.
- **Lightweight Design**: Minimal resource footprint for edge deployment.

---

## Getting Started in 3 Steps

Get your Meshtopo gateway up and running with just three commands.

1. **Clone the repository:**

    ```bash
    git clone https://github.com/clayauld/meshtopo.git
    ```

2. **Navigate into the directory:**

    ```bash
    cd meshtopo
    ```

3. **Run the setup wizard:**

    ```bash
    make setup
    ```

    The interactive wizard will guide you through creating your `config.yaml` file, entering your CalTopo connect key, and setting up the MQTT broker.

Once the setup is complete, you can start the service using Docker:

```bash
docker compose up -d
```

---

## How It Works

The system follows a simple linear data flow:

1. **Meshtastic Network** → LoRa mesh nodes with an MQTT gateway feature enabled.
2. **MQTT Broker** → A central message broker (e.g., Mosquitto) that receives data from the Meshtastic network. This can be an external broker or the one integrated with Meshtopo.
3. **Meshtopo Gateway Service** → This Python service connects to the MQTT broker, filters and transforms the data, and forwards it to CalTopo.
4. **CalTopo Team Account** → The cloud mapping platform where your devices appear in real-time.

---

## Configuration Reference

The service is configured via a single `config/config.yaml` file. The `make setup` wizard will help you create this file initially.

### Main Configuration Parameters

| Parameter                       | Description                                                                                      | Example                |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------- |
| `mqtt.broker`                   | IP address or hostname of your MQTT broker. Use `mosquitto` if using the internal broker.        | `192.168.1.100`        |
| `mqtt.port`                     | MQTT broker port.                                                                                | `1883`                 |
| `mqtt.username`                 | MQTT authentication username.                                                                    | `meshtopo_user`        |
| `mqtt.password`                 | MQTT authentication password.                                                                    | `your_secure_password` |
| `mqtt.topic`                    | MQTT topic pattern for Meshtastic position packets. **Replace `US` with your LoRa region code.** | `msh/US/2/json/+/+`    |
| `caltopo.connect_key`           | Your CalTopo Team Account connect key.                                                           | `G3rvY...`             |
| `devices.allow_unknown_devices` | If `true`, devices not listed in the `nodes` section can send position updates.                  | `true`                 |

### Node Display Name Overrides

You can optionally override the display names of your Meshtastic nodes in CalTopo.

```yaml
nodes:
    "!823a4edc": # Hardware ID from Meshtastic
        device_id: "TEAM-LEAD"
    "!a4b8c2f0":
        device_id: "COMMS-1"
```

### LoRa Region Codes

The region code in the MQTT topic must be replaced with the appropriate LoRa region code for your country. Common region codes include:

- **US** - United States
- **EU_868** - European Union (868 MHz)
- **ANZ** - Australia/New Zealand

For the complete list, see the [Meshtastic LoRa Region by Country documentation](https://meshtastic.org/docs/configuration/region-by-country/).

---

## Developer & Contributor Guide

Interested in contributing to Meshtopo? Here's how to get your development environment set up.

### Prerequisites

- Python 3.9+
- `pre-commit` for code quality checks

### Setup

1. **Install dependencies**:

    ```bash
    make install
    ```

2. **Set up the development environment**:
   This will install development dependencies and pre-commit hooks.

    ```bash
    make dev-setup
    ```

### Running Tests

Run the full test suite:

```bash
make test
```

### Code Style & Linting

The project follows PEP 8 guidelines and uses `black` for formatting and `flake8`/`mypy` for linting. The pre-commit hooks handle this automatically.

- **Run linting checks:**

    ```bash
    make lint
    ```

- **Format code:**

    ```bash
    make format
    ```

### Project Structure

```
meshtopo/
├── config/             # Configuration files and templates
├── deploy/             # Docker and deployment files
├── docs/               # Documentation
├── scripts/            # Helper scripts
├── src/                # Python source code
├── tests/              # Test suite
├── .pre-commit-config.yaml # Pre-commit hooks
├── Makefile            # Development commands
└── README.md           # This file
```

---

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

    - Verify connect key is correct
    - Check CalTopo Team Account status
    - Verify internet connectivity

4. **Devices Not Appearing in CalTopo**

    - Ensure connect key is from Team Account access URL
    - Check that nodes are sending position data
    - Verify callsign extraction from nodeinfo messages

---

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
- Review the configuration examples in `config/` directory
