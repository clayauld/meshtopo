import pytest
import subprocess
import time
import os


@pytest.fixture(scope="module")
def docker_stack():
    """
    Manages the lifecycle of the Docker Compose integration stack.
    Spins up services before tests and tears them down after.
    """
    compose_file = "deploy/docker-compose.integration.yml"

    # Ensure we are in project root
    if not os.path.exists(compose_file):
        pytest.fail(
            f"Could not find compose file at {compose_file}. Run from project root."
        )

    # 1. Setup: Start containers
    try:
        subprocess.run(
            ["docker", "compose", "-f", compose_file, "up", "-d", "--build"],
            check=True,
            capture_output=True,
        )
        # Give services a moment to initialize
        time.sleep(5)
        yield
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to start docker stack: {e.stderr}")
    finally:
        # 2. Teardown: Stop and remove containers
        subprocess.run(
            ["docker", "compose", "-f", compose_file, "down", "-v"],
            check=True,
            capture_output=True,
        )
