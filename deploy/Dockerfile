# Build stage
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY config/ config/

# Install dependencies into a temporary directory
RUN pip install --no-cache-dir --prefix=/install .

# Production stage
FROM python:3.9-slim AS production

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash meshtopo && \
    chown -R meshtopo:meshtopo /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ src/
COPY config/ config/

# Switch to non-root user
USER meshtopo

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://caltopo.com', timeout=5)" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/gateway.py"]
