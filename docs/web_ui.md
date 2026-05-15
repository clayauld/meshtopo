# MeshTopo Web Administration UI

MeshTopo includes a built-in, authenticated Web Administration UI for real-time monitoring and configuration management. This allows you to manage your gateway without manually editing configuration files or restarting the service.

## 1. Accessing the Web UI

By default, the Web UI is available at:

`http://<server-ip>:8080`

### Authentication

Access to the Web UI is protected by an admin password. You can set this password:

1. **During Setup**: Use the `scripts/setup_wizard.py` or `make setup`.
2. **Via Environment Variable**: Set `WEB_ADMIN_PASSWORD` in your `.env` file or Docker configuration.
3. **In `config.yaml`**: Set `web.admin_password`.

## 2. The Dashboard

The primary dashboard provides real-time situational awareness of your gateway:

- **Global Statistics**: Total messages received, processed, and position updates successfully sent to CalTopo.
- **Uptime**: System runtime and start timestamp.
- **Live Logs**: A real-time stream of the application's internal logs (similar to `docker logs`).
- **Device Status Table**:
  - **Hardware ID**: The canonical Meshtastic ID (e.g., `!123a4edc`).
  - **Callsign**: The display name currently being used in CalTopo.
  - **Last Seen**: Timestamp of the most recent packet from the device.
  - **Messages**: Number of packets processed for this specific device.

## 3. Tenant Management

When `web.multi_tenant_enabled` is set to `true`, the Super-User can manage multiple independent tenants.

- **Create Tenant**: Create a new organization with its own:
  - **Username/Password**: Independent login for the tenant manager.
  - **CalTopo Connect Key**: Dedicated API key for this tenant's map.
  - **MQTT Channel**: The specific Meshtastic channel name (e.g., `LongFast`) to route to this tenant.
- **Isolate Data**: Each tenant only sees and manages their own devices and logs.

## 4. Configuration Portal

The configuration portal allows for zero-downtime updates to the system state:

- **Global Settings**: Update MQTT broker details, logging levels, and unknown device policies.
- **Device Overrides**: Manually assign specific Hardware IDs to custom Callsigns or CalTopo Groups.
- **Tenant Config**: Tenant managers can update their own CalTopo keys and channel assignments.

## 5. Security Best Practices

- **Reverse Proxy**: In production, it is highly recommended to run MeshTopo behind a reverse proxy (like Traefik or Caddy) to provide SSL/TLS encryption (HTTPS).
- **Strong Passwords**: Use complex passwords for both the Global Admin and individual Tenants.
- **Internal Network**: If possible, keep the Web UI port restricted to a VPN or local management network.
