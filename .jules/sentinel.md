## 2025-02-18 - [Insecure Deserialization in State Persistence]
**Vulnerability:** `sqlitedict` was using default Pickle serialization for `node_id_mapping` and `callsign_mapping` databases. This allows arbitrary code execution if the SQLite file is tampered with.
**Learning:** `sqlitedict` defaults to pickle, even if documentation says otherwise. Always verify library defaults. Even "internal" state files can be attack vectors if volume-mounted or accessible.
**Prevention:** Explicitly use `encode=json.dumps` and `decode=json.loads` when initializing `SqliteDict` for simple data types.
