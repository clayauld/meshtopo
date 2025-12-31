# **Meshtopo Gateway: System Design & Architecture**

- **Version:** 2.0
- **Date:** January 2026
- **Status:** Active

---

## 1. Executive Summary

### 1.1 Purpose
The **Meshtopo Gateway** is a specialized integration service that bridges the gap between **Meshtastic** (off-grid LoRa mesh networks) and **CalTopo** (SAR/Emergency mapping platforms). It provides real-time situational awareness by automatically forwarding location data from field teams to a shared command map.

This document describes the system architecture, component interactions, and deployment model. It is intended for **Implementation Engineers** setting up the system and **Developers** maintaining or extending the codebase.

### 1.2 High-Level Workflow
1.  **Field Assets** transmit location data via Meshtastic nodes.
2.  An **MQTT Gateway Node** (or software bridge) forwards these packets to an MQTT Broker.
3.  The **Meshtopo Service** subscribes to the broker, filters for relevant position data, and decrypts/parses the payload.
4.  The service resolves the **Node ID** to a human-readable **Callsign**.
5.  The service pushes the location update to **CalTopo** via their API.

---

## 2. System Architecture

The system is built on a modern, asynchronous Python foundation designed for reliability, concurrency, and security.

### 2.1 Component Diagram

```mermaid
graph LR
    subgraph "Field Layer"
        NodeA[Meshtastic Node A] -- LoRa --> NodeGW[MQTT Gateway Node]
        NodeB[Meshtastic Node B] -- LoRa --> NodeGW
    end

    subgraph "Transport Layer"
        NodeGW -- WiFi/Cell --> MQTT[MQTT Broker (Mosquitto)]
    end

    subgraph "Meshtopo Service (Docker Container)"
        MQTT -- Sub --> MqttClient[Async MQTT Client]
        MqttClient -- Msg --> GatewayApp[Gateway Orchestrator]
        GatewayApp -- Read/Write --> StateDB[(Persistent State DB)]
        GatewayApp -- Position --> Reporter[CalTopo Reporter]
    end

    subgraph "Application Layer"
        Reporter -- HTTPS --> CalTopoAPI[CalTopo Cloud API]
    end
```

### 2.2 Core Modules

The application source code is modular, following the Single Responsibility Principle.

| Module | Responsibility | Key Technologies |
| :--- | :--- | :--- |
| **`gateway.py`** | **Entry Point.** Handles CLI arguments, path security validation, and starts the main event loop. | `sys`, `os` |
| **`gateway_app.py`** | **Orchestrator.** Manages the lifecycle of sub-components, routing logic, and state management. Acts as the "brain" of the operation. | `asyncio` |
| **`mqtt_client.py`** | **Ingest.** Maintains the persistent connection to the MQTT broker. Handles automatic reconnection and message decoding. | `aiomqtt`, `paho-mqtt` |
| **`caltopo_reporter.py`** | **Egress.** Manages the HTTP connection to CalTopo. Implements connection pooling, retries, and rate limiting. | `httpx` |
| **`persistent_dict.py`** | **State Persistence.** A custom, secure key-value store backed by SQLite (WAL mode) that strictly uses JSON serialization to avoid security risks. | `sqlite3`, `json` |
| **`config/config.py`** | **Configuration.** Defines the strict schema for `config.yaml` using Pydantic models. Handles environment variable overrides and secret masking. | `pydantic`, `PyYAML` |

---

## 3. Data Flow & Logic

### 3.1 Message Processing Pipeline

1.  **Ingestion:** The `MqttClient` receives a raw byte payload from the subscribed topic (e.g., `msh/US/2/json/+/+`).
2.  **Decoding:** The payload is decoded to a JSON object. The `type` field is inspected.
3.  **Routing (`GatewayApp`):**
    *   **`nodeinfo` packet:** Contains metadata (Long Name, Short Name, Hardware ID). The app updates the `StateDB` to map the numeric Node ID to the Hardware ID and Callsign.
    *   **`position` packet:** Contains coordinates. The app looks up the sender in the `StateDB`.
        *   *If known:* The Callsign is retrieved.
        *   *If unknown:* The packet is dropped (unless `allow_unknown_devices` is enabled).
4.  **Reporting (`CalTopoReporter`):**
    *   The reporter constructs the API URL.
    *   It sends the request asynchronously.
    *   **Reliability:** If the API fails (5xx or 429), it enters a retry loop with exponential backoff (1s, 2s, 4s...).

### 3.2 State Persistence Strategy
The gateway is stateless *logic* but maintains stateful *data* about the mesh network.
*   **Problem:** Meshtastic nodes transmit their "Node Info" (Name) infrequently, but "Position" frequently. If the gateway restarts, it might receive a position from a node it hasn't "met" yet.
*   **Solution:** The `PersistentDict` module stores learned mappings in `meshtopo_state.sqlite`. This file persists across container restarts, ensuring immediate recognition of known nodes.

---

## 4. Security & Reliability Features

### 4.1 Security Controls
*   **Input Validation:**
    *   **Configuration:** `gateway.py` prevents directory traversal attacks by validating config file paths.
    *   **SSRF Prevention:** `CalTopoReporter` enforces strict URL allowlisting (defaulting to `*.caltopo.com`) to prevent the gateway from attacking internal networks.
    *   **Log Injection:** `utils.sanitize_for_log` strips control characters from untrusted input before logging.
*   **Secret Management:**
    *   Passwords and keys are handled using Pydantic's `SecretStr`, preventing them from being accidentally printed in logs or stack traces.
    *   The `PersistentDict` implementation replaces insecure Python `pickle` serialization with strict `json`, mitigating code execution vulnerabilities.

### 4.2 Resilience
*   **Non-Blocking I/O:** The system uses Python's `asyncio` loop. A slow CalTopo API response does *not* block the MQTT listener.
*   **Connection Pooling:** `httpx.AsyncClient` is reused across requests, maintaining persistent TCP/TLS connections to CalTopo for lower latency.
*   **Database Concurrency:** SQLite is configured in **WAL (Write-Ahead Logging)** mode, allowing non-blocking concurrent reads and writes.

---

## 5. Deployment Guide

### 5.1 Docker Compose
The recommended deployment uses Docker Compose. The stack can be configured in three "profiles" depending on your needs.

| Profile | Services | Use Case |
| :--- | :--- | :--- |
| **`core`** | `meshtopo-gateway` | You already have an MQTT broker. You just need the bridge. |
| **`mqtt`** | `core` + `mosquitto` | You need a self-hosted MQTT broker for your mesh. |
| **`ssl`** | `mqtt` + `caddy` | You need the broker to be accessible over the public internet with secure WebSockets (WSS). |

### 5.2 Configuration
The system is configured via `config/config.yaml`. Environment variables can override any setting (ideal for Kubernetes or secure credential injection).

**Example: Overriding Secrets**
```yaml
# config.yaml
mqtt:
  password: "placeholder_password"
```
Env Var: `MQTT_PASSWORD=RealSecurePassword123!`

---

## 6. Monitoring & Troubleshooting

### 6.1 Logging
Logs are structured for easy parsing.
*   **INFO:** Normal operation (connection events, position sent).
*   **WARNING:** Transient issues (API timeout - retrying, unknown node).
*   **ERROR:** Fatal issues (Config invalid, Disk full).

### 6.2 Health Checks
The Docker container exposes a health check that verifies connectivity to the CalTopo API.
`docker inspect --format='{{json .State.Health}}' meshtopo-gateway`

### 6.3 Common Issues
1.  **"Unknown Device" Logs:** The gateway is receiving positions from a node it hasn't seen a `nodeinfo` packet for yet. *Remediation:* Wait for the node to beacon (or force a refresh), or manually add the ID to `config.yaml`.
2.  **"Permission Denied" on SQLite:** Ensure the Docker volume is writable by the container user (UID 1000).
