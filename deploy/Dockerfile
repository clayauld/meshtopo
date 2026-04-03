# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc wget tar \
    && rm -rf /var/lib/apt/lists/*

# Download and extract Litestream
ARG LS_VERSION=0.5.7
RUN wget -q https://github.com/benbjohnson/litestream/releases/download/v${LS_VERSION}/litestream-${LS_VERSION}-linux-x86_64.tar.gz \
    && tar -xzf litestream-${LS_VERSION}-linux-x86_64.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/litestream

COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY config/ config/

# Install dependencies into a temporary directory
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir --prefix=/install .

# Production stage
FROM python:3.10-slim AS production

WORKDIR /app

# Install runtime dependencies for Unraid/PUID/PGID support
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash meshtopo && \
    mkdir -p /app/data /app/logs && \
    chown -R meshtopo:meshtopo /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy litestream from builder
COPY --from=builder /usr/local/bin/litestream /usr/local/bin/litestream

# Copy application code
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/

# Ensure scripts are executable
RUN chmod +x scripts/*.sh

# Switch to non-root user (removed for entrypoint handling)
# USER meshtopo

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://caltopo.com', timeout=5)" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV STORAGE_DB_PATH=/app/data/meshtopo_state.sqlite

# Default command uses the entrypoint script
CMD ["/bin/bash", "/app/scripts/entrypoint.sh"]
