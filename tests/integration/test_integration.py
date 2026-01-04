
import asyncio
import os
import shutil
import subprocess
import time

import httpx
import pytest

# Check if docker is available
def is_docker_available():
    return shutil.which("docker") is not None

# Check if we have permission to use docker (e.g. socket access)
def can_run_docker():
    if not is_docker_available():
        return False
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@pytest.mark.integration
@pytest.mark.skipif(not can_run_docker(), reason="Docker not available or no permission")
def test_end_to_end_flow(docker_stack):
    """
    Full integration test:
    1. Spin up Mosquitto + Gateway
    2. Publish MQTT message
    3. Verify Gateway processes it (via logs or mock endpoint)

    For now, we just verify the container starts healthy.
    """
    # Wait for health
    time.sleep(5)

    # Check if container is running
    result = subprocess.run(
        ["docker", "compose", "-f", "deploy/docker-compose.integration.yml", "ps", "-q", "meshtopo-gateway"],
        capture_output=True,
        text=True
    )
    assert result.stdout.strip()

    # Note: Testing the actual API call to CalTopo in integration requires a mock server
    # which is out of scope for this basic test, but we know the container started.
