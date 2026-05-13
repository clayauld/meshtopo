# MQTT Topic Structure and Routing

MeshTopo uses MQTT to receive real-time data from Meshtastic nodes. Understanding the topic structure is critical for proper configuration and multi-tenant routing.

## Meshtastic MQTT Topic Standard

Meshtastic nodes configured with the MQTT module enabled and "JSON Output" turned ON will publish messages to topics following this pattern:

`msh/<region>/2/json/<channel_name>/<node_id>`

### Breakdown

- **`msh`**: The root topic (configurable in Meshtastic, but defaults to `msh`).
- **`<region>`**: The LoRa region code (e.g., `US`, `EU_868`, `ANZ`).
- **`2`**: The Protobuf version / MQTT schema version.
- **`json`**: Indicates that the payload is in JSON format.
- **`<channel_name>`**: The name of the Meshtastic channel (e.g., `LongFast`, `Team-Alpha`).
- **`<node_id>`**: The hardware ID of the sending node (e.g., `!123a4edc`).

## Message Types

MeshTopo processes the following JSON message types:

1. **`position`**: GPS coordinates and altitude. Used to update markers in CalTopo.
2. **`nodeinfo`**: Device names (long/short), hardware details, and role. Used to automatically name devices in CalTopo.
3. **`telemetry`**: Battery level, voltage, and environment sensors.
4. **`traceroute`**: Mesh path information between nodes.

## Multi-Tenant Routing

MeshTopo supports two methods for routing data to different CalTopo accounts in a multi-tenant environment:

### 1. Hardware ID Mapping (Default)

Each node is explicitly mapped to a tenant in the MeshTopo Web UI. This is useful for fixed teams where hardware is rarely swapped.

### 2. Topic-Based Routing (Advanced)

Nodes can be routed based on the **`<channel_name>`** segment of the MQTT topic.

- **Example**: A tenant named "AlphaTeam" can be configured with an `mqtt_channel` of `Alpha-Channel`.
- Any message arriving on `msh/US/2/json/Alpha-Channel/` will be automatically routed to AlphaTeam's CalTopo account, regardless of which hardware ID sent it.

This is ideal for field deployments where multiple teams share the same broker but operate on different Meshtastic channels.

## Configuration

### Global Configuration

In your `config.yaml`, the `mqtt.topic` parameter defines what the gateway listens to.

- **Single Topic**: `topic: "msh/US/2/json/+/+"` (listens to all channels in the US region).
- **Multiple Topics**:

  ```yaml
  mqtt:
    topic:
      - "msh/US/2/json/+/+"
      - "msh/EU_868/2/json/+/+"
  ```

### Web UI / Admin Portal

The mapping between an MQTT channel and a tenant can be managed directly in the Web UI:

1. **Admin Portal**: When creating a new tenant, a super-user can specify the `Meshtastic MQTT Channel`.
2. **Tenant Configuration**: Individual tenants can update their assigned `Meshtastic MQTT Channel` in their own configuration dashboard.

Any traffic arriving on the specified channel will be automatically routed to that tenant's CalTopo account.

## Troubleshooting

- **No data appearing**: Ensure "JSON Output" is enabled on your Meshtastic MQTT gateway node. MeshTopo does **not** support Protobuf payloads.
- **Wrong Region**: Ensure your `mqtt.topic` in `config.yaml` matches the region configured on your radios.
