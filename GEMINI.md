# GEMINI.md

## Project Overview

This project, `meshtopo`, is a Python-based gateway service that bridges Meshtastic LoRa mesh networks with CalTopo mapping platforms. Its primary purpose is to enable real-time position tracking of field assets on high-quality maps.

The service is designed to be lightweight and easy to deploy, with a focus on Docker-based deployment. It acts as a reliable bridge, forwarding location data from Meshtastic nodes directly to CalTopo maps, providing real-time situational awareness.

**Key Technologies:**

* **Programming Language:** Python 3.9+
* **Core Libraries:**
  * `asyncio-mqtt`: For asynchronous MQTT communication.
  * `httpx`: For asynchronous HTTP requests to the CalTopo API.
  * `pydantic`: For data validation and configuration management.
  * `sqlitedict`: for persistent storage of node and callsign mappings.
* **Deployment:** Docker, Docker Compose
* **Development Tools:**
  * `pytest`: For testing.
  * `pre-commit`: For code quality checks (black, flake8, isort, mypy).

**Architecture:**

The application follows a simple, linear data flow:

1. **Meshtastic Network:** LoRa mesh nodes with the MQTT gateway feature enabled send data to an MQTT broker.
2. **MQTT Broker:** A central message broker (e.g., Mosquitto) receives data from the Meshtastic network.
3. **Meshtopo Gateway Service:** This Python service connects to the MQTT broker, filters and transforms the data, and forwards it to CalTopo.
4. **CalTopo Team Account:** The cloud mapping platform where devices appear in real-time.

The core logic is encapsulated in the `GatewayApp` class (`src/gateway_app.py`), which orchestrates the MQTT client and the CalTopo reporter. The application is highly configurable via a `config.yaml` file.

## Building and Running

### Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/clayauld/meshtopo.git
    cd meshtopo
    ```

2. **Run the setup wizard:**

    ```bash
    make setup
    ```

    This will guide you through creating your `config.yaml` file.

### Running the Service

* **Using Docker (recommended):**

    ```bash
    docker compose up -d
    ```

* **Running directly:**

    ```bash
    make run
    ```

### Running Tests

* **Run all tests:**

    ```bash
    make test-full
    ```

* **Run tests without integration tests:**

    ```bash
    make test
    ```

## Development Conventions

* **Development Environment:** It is highly recommended to use a Python virtual environment (venv) to manage project dependencies. This isolates the project's dependencies from your system's Python packages.

* **Code Style:** The project follows PEP 8 guidelines and uses `black` for formatting and `isort` for import sorting.
* **Linting:** `flake8` and `mypy` are used for linting and type checking.
* **Pre-commit Hooks:** The project uses pre-commit hooks to automatically enforce code style and linting before each commit.
* **Configuration:** Application configuration is managed through a `config.yaml` file, with schema validation performed by `pydantic`.
* **Dependencies:** Project dependencies are managed in `pyproject.toml`.
* **Makefile:** A comprehensive `Makefile` provides commands for common development tasks such as installation, testing, and deployment.
