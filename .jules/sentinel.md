# Sentinel Learnings

## 2025-02-18 - [Insecure Deserialization in State Persistence]

**Vulnerability:** `sqlitedict` was using default Pickle serialization for `node_id_mapping` and `callsign_mapping` databases. This allows arbitrary code execution if the SQLite file is tampered with.
**Learning:** `sqlitedict` defaults to pickle, even if documentation says otherwise. Always verify library defaults. Even "internal" state files can be attack vectors if volume-mounted or accessible.
**Prevention:** Explicitly use `encode=json.dumps` and `decode=json.loads` when initializing `SqliteDict` for simple data types.

## 2025-12-19 - [Log Injection via MQTT Payloads]

**Vulnerability:** Raw MQTT payloads and derived identifiers (callsigns) were logged directly, allowing attackers to inject fake log entries via newlines.
**Learning:** Even internal identifiers like `callsign` can be tainted if derived from external sources (Meshtastic nodeinfo).
**Prevention:** Use a dedicated sanitization utility (`sanitize_for_log`) for all data originating from external sources before logging.
