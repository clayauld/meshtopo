# MQTT Topic Structure and Routing

MeshTopo uses MQTT to receive real-time data from Meshtastic nodes. Understanding the topic structure is critical for proper configuration and multi-tenant routing.

## Meshtastic MQTT Topic Standard

Meshtastic nodes configured with the MQTT module enabled publish messages to topics following one of these patterns:

- **JSON Format**: `msh/<region>/2/json/<channel_name>/<node_id>`
- **Cleartext Protobuf**: `msh/<region>/2/c/<channel_name>/<node_id>`
- **Encrypted Protobuf**: `msh/<region>/2/e/<channel_name>/<node_id>`

### Breakdown

- **`msh`**: The root topic (configurable in Meshtastic, but defaults to `msh`).
- **`<region>`**: The LoRa region code (e.g., `US`, `EU_868`, `ANZ`).
- **`2`**: The Protobuf version / MQTT schema version.
- **`json` / `c` / `e`**: The data format:
  - `json`: Human-readable JSON.
  - `c`: Cleartext binary Protobuf.
  - `e`: Encrypted binary Protobuf (AES-CTR).
- **`<channel_name>`**: The name of the Meshtastic channel (e.g., `LongFast`, `Team-Alpha`).
- **`<node_id>`**: The hardware ID of the sending node (e.g., `!123a4edc`).

## Data Decryption (Protobuf 'e')

When receiving encrypted Protobuf messages (`e`), MeshTopo automatically attempts to decrypt them using the standard Meshtastic AES-CTR mechanism.

### The Decryption Process

1. **Key Lookup**: The gateway checks for a channel-specific key in the tenant configuration or the `crypto.channel_keys` section of `config.yaml`.
2. **Default Key**: If no specific key is found, it falls back to the default Meshtastic `LongFast` key (`1OAMXnSjM/I69sPByKxGzQ==`).
3. **Nonce Construction**: The AES-CTR nonce (128-bit IV) is constructed as follows:
   - **Bytes 0-7**: Packet ID (64-bit integer, Little-Endian)
   - **Bytes 8-11**: Sender Node ID (32-bit integer, Little-Endian)
   - **Bytes 12-15**: Zero padding (`\x00\x00\x00\x00`)

This precise construction is critical for interoperability with Meshtastic's `CryptoEngine`.

### Secure Channels

By supporting encrypted Protobufs, MeshTopo allows organizations to maintain full end-to-end encryption on their LoRa mesh while still benefiting from centralized mapping.

## Message Types

MeshTopo processes the following message types (JSON or Protobuf):

1. **`position`**: GPS coordinates and altitude. Used to update markers in CalTopo.
2. **`nodeinfo`**: Device names (long/short), hardware details, and role. Used to automatically name devices in CalTopo.
3. **`telemetry`**: Battery level, voltage, and environment sensors.
4. **`traceroute`**: Mesh path information between nodes.

## Multi-Tenant Routing

MeshTopo supports two methods for routing data to different CalTopo accounts in a multi-tenant environment:

### 1. Hardware ID Mapping (Default)

Each node is explicitly mapped to a tenant in the MeshTopo Web UI. This is useful for fixed teams where hardware is rarely swapped.

### 2. Topic-Based Routing (Recommended for Scale)

Nodes can be routed based on the **`<channel_name>`** segment of the MQTT topic. This allows for dynamic "plug-and-play" multi-tenancy.

- **How it works**: A tenant is configured with a specific `Meshtastic MQTT Channel` (e.g., `SAR-Team-1`).
- **Routing**: Any message arriving on an MQTT topic containing that channel name (e.g., `msh/US/2/json/SAR-Team-1/...`) is automatically routed to that tenant's CalTopo account.
- **Benefits**: No need to manually map individual hardware IDs. New radios added to the physical LoRa channel will automatically appear on the correct map.

### 3. Broadcast Routing

If `unknown_devices_all_tenants` is enabled, any message from a device that is **not** specifically mapped to a tenant will be forwarded to **all** active tenants. This is useful for shared infrastructure or monitoring common public channels (like `LongFast`).

## Configuration

### Global Configuration

In your `config.yaml`, the `mqtt.topic` parameter defines what the gateway listens to.

- **Single Topic**: `topic: "msh/US/2/+/+/+"` (listens to all formats and channels in the US region).
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

- **No data appearing**: Ensure your Meshtastic MQTT gateway node is correctly connected to the broker and has uplink enabled for the desired channels.
- **Wrong Region**: Ensure your `mqtt.topic` in `config.yaml` matches the region configured on your radios.
