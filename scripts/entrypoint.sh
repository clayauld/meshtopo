#!/bin/bash
set -e

if [ "$AZURE_LITESTREAM" = "true" ]; then
    echo "Litestream enabled. Generating configuration..."

    # Generate litestream config in a writable location
    # We use 'EOF' to prevent bash from expanding variables; Litestream expands them natively.
    cat <<'EOF' > /tmp/litestream.yml
dbs:
  - path: /app/data/meshtopo_state.sqlite
    replicas:
      - type: abs
        bucket: ${AZURE_STORAGE_CONTAINER}
        account-name: "${AZURE_STORAGE_ACCOUNT}"
        account-key: "${AZURE_STORAGE_KEY}"
        path: pb_data.db
        validation-interval: "1h"
EOF

    echo "Starting Litestream replication..."
    if [ ! -f "/app/data/meshtopo_state.sqlite" ]; then
        echo "No local database found. Attempting restore..."
        litestream restore -if-replica-exists -config /tmp/litestream.yml /app/data/meshtopo_state.sqlite
        echo "Restore complete."
    else
        echo "Local database found. Skipping restore."
    fi
    exec litestream replicate -config /tmp/litestream.yml -exec "python src/gateway.py"
else
    echo "Litestream disabled. Starting application directly..."
    exec python src/gateway.py
fi
