# Migrating MeshTopo to Litestream

This guide provides the steps required to migrate your `meshtopo` Azure Container App deployment to utilize Litestream for SQLite database backups to Azure Blob Storage, matching the deployment style used in `sar-respond`.

## 1. Create Azure Storage Resources

You will need a dedicated Blob Storage container where Litestream can store its database replicas.

1. In the Azure Portal, navigate to your Storage Account (or create a new one).
2. Create a new Blob Container (e.g., `meshtopo-litestream-backup`).
3. Under **Access keys**, copy the value of `key1` or `key2`. You will need this for the container app secrets.

## 2. Update `config.yaml`

Because Litestream expects to find the local SQLite database at `/app/data/meshtopo_state.sqlite` (as configured in the container app's `EmptyDir` mount), you MUST update your meshtopo configuration file to point to this new location.

1. Open your `config.yaml` file (hosted on the Azure File Share mounted at `mosquitto-config`).
2. Add or update the `storage` block:

```yaml
storage:
  db_path: /app/data/meshtopo_state.sqlite
```

_(If this is not updated, meshtopo will store its DB in the container root, which will not align with Litestream's replication path)._

## 3. Apply the Updated Container App Configuration

The `meshtopo-azure.yaml` file has been updated to include:

- Litestream environment variables (`AZURE_LITESTREAM`, `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_CONTAINER`).
- A new Azure Container App secret for `AZURE_STORAGE_KEY`.
- A new `EmptyDir` volume named `meshtopo-data` mounted at `/app/data` to host the ephemeral SQLite file.

Before deploying, update the placeholders in `meshtopo-azure.yaml`:

- Replace `<YOUR_STORAGE_KEY>` under the `secrets` section.
- Replace `<YOUR_STORAGE_ACCOUNT>` and `<YOUR_CONTAINER_NAME>` under the `meshtopo-gateway` environment variables.

Deploy using the Azure CLI:

```bash
az containerapp update \
  --name meshtopo \
  --resource-group AMRG-Infrastructure-RG \
  --yaml meshtopo-azure.yaml
```

## 4. Verify the Deployment

With the new `scripts/entrypoint.sh` baked into the `latest` image:

1. View the container app's log stream for `meshtopo-gateway` in the Azure Portal.
2. You should see logs indicating Litestream is enabled:

```
Litestream enabled. Generating configuration...
Starting Litestream replication...
No local database found. Attempting restore...
...
```

1. Once running, log into Azure portal and verify that the `.db` / replica chunks have appeared in your Azure Storage Container.
