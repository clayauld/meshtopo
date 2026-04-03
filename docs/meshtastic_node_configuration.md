# Meshtastic Node Configuration Guide

To successfully bridge your Meshtastic LoRa network with CalTopo using the Meshtopo gateway, you must properly configure your Meshtastic hardware. 

The network requires two distinct configurations:
1. **The Field Nodes**: The mobile radios carried by out-of-band personnel.
2. **The MQTT Gateway Node**: The permanent or semi-permanent radio connected to both the LoRa mesh and a TCP/IP network (WiFi or Ethernet).

---

## 1. The MQTT Gateway Node Configuration

This is the bridge device. It listens to the LoRa mesh and forwards that traffic to your MQTT broker, which the Meshtopo Python service then reads.

### Network Settings (WiFi / Ethernet)
Ensure the node is connected to the same local area network as your MQTT Broker (or has internet access if using a cloud broker).
- **WiFi Enabled:** `True`
- **SSID:** Your WiFi Network 
- **PSK:** Your WiFi Password

### MQTT Module Settings
Use the Meshtastic CLI, Web UI, or Smartphone App to configure the MQTT module:
- **Enabled:** `True`
- **Address:** The IP address or hostname of your MQTT Broker. *(e.g., `192.168.1.100`)*
- **Port:** `1883` *(or `8883` if using TLS)*
- **Username:** Your MQTT user as defined in the Meshtopo configuration.
- **Password:** Your MQTT password.
- **Root Topic:** Typically `msh`.
- **JSON Output Enabled:** `True` (Critical: Meshtopo requires JSON payloads, not Protobufs).

### Channel Settings (Uplink/Downlink)
For the MQTT node to bridge data correctly, it must have permission to uplink channel traffic.
- **Role:** Typically set to `CLIENT` or `ROUTER` depending on its location.
- **Primary Channel (LongFast, etc.):** 
  - **Uplink Enabled:** `True` (Forwards field radio data to the MQTT broker)
  - **Downlink Enabled:** `False` (Recommended to disable to prevent internet-to-LoRa spam, since Meshtopo is purely a receiving service right now).

---

## 2. The Field Nodes Configuration

Field nodes are the actual assets moving on the map. They require very little special configuration outside of normal Meshtastic operation.

### General & Position Settings
- **Role:** `CLIENT` or `TRACKER` (depending on whether it has a screen/user or is purely a relay/tracker).
- **Position Broadcasting:** Ensure GPS is enabled and broadcasting.
  - **Smart Position:** Recommended `True`.
  - **Broadcast Interval:** Set according to your needs (e.g., 120 seconds or higher depending on channel utilization).

### Identification
Meshtopo relies heavily on the names provided by the nodes to map them to CalTopo identifiers.
- **Long Name:** Set this to your desired identifier (e.g., `Team Alpha`, `Medic-1`). Meshtopo will use this to establish a CalTopo Callsign automatically if a manual override isn't configured in the Web UI.
- **Short Name:** Set to an appropriate 4-character identifier.

### Channels
- The field nodes must share the exact same Channel settings (Name, PSK, Modem Preset) as the MQTT Gateway node so their telemetry can be actively bridged.
- **Uplink/Downlink:** By default, field nodes do not need MQTT enabled on their individual configurations, as the central Gateway Node handles the bridge. However, their implicit channel settings must permit their traffic to be routed.

---

## 3. Verifying the Connection

Once both the Field Nodes and the MQTT Gateway Node are configured:
1. Turn on a Field Node and wait for a GPS lock.
2. Watch the Meshtopo Web UI Dashboard or system logs.
3. You should see `"Messages Received"` increment, indicating that the Gateway Node is successfully receiving LoRa traffic, converting it to JSON, pushing it to the MQTT Broker, and being consumed by Meshtopo.
