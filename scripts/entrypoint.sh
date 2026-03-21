#!/bin/bash
set -e

if [ "$AZURE_LITESTREAM" = "true" ]; then
    echo "Litestream enabled. Generating configuration..."
    
    # Dynamically extract the configured database path using Python
    # This ensures Litestream backs up the actual file configured by the user
    DB_PATH=$(python3 -c "
import os, yaml
try:
    with open('config/config.yaml') as f:
        path = yaml.safe_load(f).get('storage', {}).get('db_path', 'data/meshtopo_state.sqlite')
        print(os.path.abspath(path))
except:
    print('/app/data/meshtopo_state.sqlite')
" 2>/dev/null || echo "/app/data/meshtopo_state.sqlite")

    echo "Using database path for Litestream: $DB_PATH"
    
    # Generate litestream config in a writable location
    # We use unquoted EOF to expand $DB_PATH, while escaping \${VAR} so Litestream natively expands them.
    cat <<EOF > /tmp/litestream.yml
dbs:
  - path: $DB_PATH
    replicas:
      - type: abs
        bucket: \${AZURE_STORAGE_CONTAINER}
        account-name: "\${AZURE_STORAGE_ACCOUNT}"
        account-key: "\${AZURE_STORAGE_KEY}"
        path: pb_data.db
        validation-interval: "1h"
EOF

    echo "Starting Litestream replication..."
    exec litestream replicate -config /tmp/litestream.yml -exec "python src/gateway.py"
else
    echo "Litestream disabled. Starting application directly..."
    exec python src/gateway.py
fi
