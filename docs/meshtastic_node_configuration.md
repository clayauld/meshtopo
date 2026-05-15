# Meshtastic Node Configuration Guide

To successfully bridge your Meshtastic LoRa network with CalTopo using the MeshTopo gateway, you must properly configure your Meshtastic hardware.

The network requires two distinct configurations:

1. **The Field Nodes**: The mobile radios carried by out-of-band personnel.
2. **The MQTT Gateway Node**: The permanent or semi-permanent radio connected to both the LoRa mesh and a TCP/IP network (WiFi or Ethernet).

---

## 1. The MQTT Gateway Node Configuration

This is the bridge device. It listens to the LoRa mesh and forwards that traffic to your MQTT broker, which the MeshTopo Python service then reads.

### Network Settings (WiFi / Ethernet)

Ensure the node is connected to the same local area network as your MQTT Broker (or has internet access if using a cloud broker).

- **WiFi Enabled:** `True`
- **SSID:** Your WiFi Network
- **PSK:** Your WiFi Password

### MQTT Module Settings

Use the Meshtastic CLI, Web UI, or Smartphone App to configure the MQTT module:

- **Enabled:** `True`
- **Address:** The IP address or hostname of your MQTT Broker. _(e.g., `192.168.1.100`)_
- **Port:** `1883` _(or `8883` if using TLS)_
- **Username:** Your MQTT user as defined in the MeshTopo configuration.
- **Password:** Your MQTT password.
- **Root Topic:** Typically `msh`.
- **JSON Output Enabled:** Optional. MeshTopo supports both JSON and binary Protobuf (Cleartext or Encrypted) formats. Using Protobuf is generally recommended for reduced bandwidth utilization.

### Channel Settings (Uplink/Downlink)

For the MQTT node to bridge data correctly, it must have permission to uplink channel traffic.

- **Role:** Typically set to `CLIENT` or `ROUTER`.
- **Primary/Secondary Channels:**
  - **Uplink Enabled:** `True` (Forwards field radio data to the MQTT broker).
  - **Downlink Enabled:** `False` (Recommended to disable to prevent internet-to-LoRa spam).

### Private Channels and Encryption

If you are using a private channel with a custom Pre-Shared Key (PSK):
1. Ensure the **Gateway Node** has the channel configured with the correct PSK.
2. MeshTopo will receive these as "Encrypted Protobufs" (`e` topics).
3. You must provide the base64 PSK to MeshTopo (via `config.yaml` or the Web UI) so it can decrypt the position reports.

---

## 2. The Field Nodes Configuration

Field nodes are the actual assets moving on the map. They require very little special configuration outside of normal Meshtastic operation.

### General & Position Settings

- **Role:** `CLIENT` or `TRACKER` (depending on whether it has a screen/user or is purely a relay/tracker).
- **Position Broadcasting:** Ensure GPS is enabled and broadcasting.
  - **Smart Position:** Recommended `True`.
  - **Broadcast Interval:** Set according to your needs (e.g., 120 seconds or higher depending on channel utilization).

### Identification

MeshTopo relies heavily on the names provided by the nodes to map them to CalTopo identifiers.

- **Long Name:** Set this to your desired identifier (e.g., `Team Alpha`, `Medic-1`). MeshTopo will use this to establish a CalTopo Callsign automatically if a manual override isn't configured in the Web UI.
- **Short Name:** Set to an appropriate 4-character identifier.

### Channels

- The field nodes must share the exact same Channel settings (Name, PSK, Modem Preset) as the MQTT Gateway node so their telemetry can be actively bridged.
- **MQTT Channel Name**: The name you give your channel in the Meshtastic app (e.g., `Team-Alpha`) is what appears in the MQTT topic. This name is used by MeshTopo for **Topic-Based Multi-Tenant Routing**. Ensure it matches the "MQTT Channel" configured in the MeshTopo Web UI.
- **Uplink/Downlink:** By default, field nodes do not need MQTT enabled on their individual configurations, as the central Gateway Node handles the bridge. However, their implicit channel settings must permit their traffic to be routed.

---

## 3. Verifying the Connection

Once both the Field Nodes and the MQTT Gateway Node are configured:

1. Turn on a Field Node and wait for a GPS lock.
2. Watch the MeshTopo Web UI Dashboard or system logs.
3. You should see `"Messages Received"` increment, indicating that the Gateway Node is successfully receiving LoRa traffic, converting it to JSON, pushing it to the MQTT Broker, and being consumed by MeshTopo.
