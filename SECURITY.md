# Security Policy & Architecture

This document outlines the security posture, cryptographic handling, and threat model of the MeshTopo gateway service.

## Authentication & Passwords

The system uses passwords to protect access to the Web Configuration Dashboard:

* **Admin / Super-User Password:** Used to access the global system settings.
* **Tenant Passwords:** Used by individual tenants to access their specific node and channel mappings.

**Storage Security:**
All authentication passwords are **cryptographically hashed** using `bcrypt` before being stored in the `meshtopo_state.sqlite` database.

* The system never stores these passwords in clear text.
* If an attacker gains read access to the SQLite database, they cannot reverse the hashes to discover the passwords.

## Meshtastic Channel Keys (PSKs)

The gateway requires Meshtastic Pre-Shared Keys (PSKs) to decipher encrypted Protobuf payloads arriving over MQTT.

**Storage Security:**
Unlike authentication passwords, symmetric encryption keys (PSKs) **must be stored in clear text** (or in a reversible format) so the gateway can mathematically perform AES decryption on incoming messages.

* PSKs are saved precisely as entered into the Web UI (or defined in `config.yaml`) within the `meshtopo_state.sqlite` database.
* **Threat Model:** If an attacker gains read access to the SQLite file or `config.yaml`, they will be able to view the PSKs. With these keys, they could decrypt your channel traffic or spoof messages onto your channel.

**Why is it built this way?**
This is the standard architectural security model for self-hosted edge services (e.g., Home Assistant, Node-RED, Mosquitto). While the system could theoretically encrypt the SQLite database using a "Master Key", that Master Key would then need to be stored in clear text on the filesystem to allow the service to start automatically unattended (the "Secret Zero" problem).

## Securing Your Deployment

The security of your MeshTopo PSKs and CalTopo API Connect Keys relies entirely on **Filesystem-Level Security** and **Network Isolation**.

To ensure your gateway remains secure:

1. **Secure the Host OS:** Ensure the server hosting the Docker containers (e.g., Linux, Unraid) is secure and SSH access is restricted.
2. **Restrict Volume Access:** Do not expose the Docker volume containing your configuration and SQLite database (e.g., `/app/data/`) to the public internet or untrusted network shares. Ensure the folder has strict permissions (`chmod 700`).
3. **Use MQTT TLS:** Ensure your MQTT broker requires authentication and utilizes TLS (Port 8883) so attackers cannot intercept raw traffic in transit.
4. **Strong Admin Password:** Set a strong `WEB_ADMIN_PASSWORD` to prevent unauthorized users from accessing the Web UI and viewing your active configuration.

## Reporting a Vulnerability

If you discover a security vulnerability within the MeshTopo Gateway codebase, please open an Issue on GitHub or contact the maintainers directly.
