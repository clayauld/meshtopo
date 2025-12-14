import json
import logging
import subprocess
import time

import httpx
import pytest
from paho.mqtt import client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MOCK_SERVER_URL = "http://localhost:8080"
TEST_TOPIC = "msh/US/2/json/TestNode/!1234abcd"
# Protobuf payload
# JSON payload (Gateway expects JSON)
TEST_MESSAGE_DICT = {
    "from": 123456789,
    "type": "position",
    "sender": "!1234abcd",
    "payload": {
        "latitude_i": 407828647,
        "longitude_i": -739653551,
        "altitude": 100,
        "time": 1600000000,
    },
}
TEST_MESSAGE = json.dumps(TEST_MESSAGE_DICT)


def wait_for_services(timeout=60):
    """
    Wait for services to be ready by polling health endpoints.

    Args:
        timeout: Maximum seconds to wait for services
    """
    start_time = time.time()

    # Wait for mock server
    logger.info("Waiting for mock server to be ready...")
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{MOCK_SERVER_URL}/reports", timeout=2.0)
            if response.status_code == 200:
                logger.info("Mock server is ready")
                break
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.RemoteProtocolError,
        ):
            time.sleep(0.5)
    else:
        raise TimeoutError("Mock server did not become ready in time")

    # Wait for MQTT broker
    logger.info("Waiting for MQTT broker to be ready...")
    while time.time() - start_time < timeout:
        try:
            test_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "health_check")
            test_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            test_client.disconnect()
            logger.info("MQTT broker is ready")
            break
        except Exception:
            time.sleep(0.5)
    else:
        raise TimeoutError("MQTT broker did not become ready in time")

    # Give gateway a moment to initialize after dependencies are ready
    logger.info("Services ready, waiting for gateway initialization...")
    time.sleep(2)


@pytest.fixture(scope="module")
def docker_stack():
    """Fixture to spin up and tear down the integration test stack."""
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "deploy/docker-compose.integration.yml",
            "down",
            "-v",
        ],
        check=True,
    )
    logger.info("Starting Docker Compose stack...")
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "deploy/docker-compose.integration.yml",
            "up",
            "-d",
            "--force-recreate",
            "--build",
        ],
        check=True,
    )

    # Wait for services to be ready
    logger.info("Waiting for services to initialize...")
    wait_for_services()

    yield

    logger.info("Dumping Gateway Logs...")
    subprocess.run(["docker", "logs", "deploy-gateway-1"], check=False)
    logger.info("Stopping Docker Compose stack...")
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "deploy/docker-compose.integration.yml",
            "down",
            "-v",
        ],
        check=True,
    )


@pytest.mark.integration
def test_end_to_end_flow(docker_stack):
    """
    Test the full flow:
    1. Publish MQTT message
    2. Gateway processes it
    3. Gateway sends HTTP report to mock server
    4. Verify report content
    """
    # 1. Clear previous reports
    logger.info("Clearing mock server reports...")
    try:
        httpx.get(f"{MOCK_SERVER_URL}/clear", timeout=5.0)
    except httpx.ConnectError:
        pytest.fail("Could not connect to mock server. Is it running?")
    except httpx.TimeoutException:
        pytest.fail("Timeout connecting to mock server.")

    # 2. Publish MQTT Message
    logger.info(f"Publishing message to {TEST_TOPIC}...")

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"Failed to connect: {reason_code}")
            return
        logger.info("Connected to MQTT Broker!")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "integration_test_publisher")
    client.on_connect = on_connect

    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT)
        logger.info("Publishing message...")
        client.publish(TEST_TOPIC, TEST_MESSAGE)
        client.loop_start()
        logger.info("Waiting for message processing...")
        time.sleep(5)  # Increased wait time
        client.loop_stop()
        logger.info("MQTT publish complete.")
    except Exception as e:
        pytest.fail(f"MQTT Publish failed: {e}")

    # 3. Verify Report
    logger.info("Verifying report reception...")
    # Give the gateway some time to process
    time.sleep(2)

    try:
        logger.info("Querying mock server for reports...")
        response = httpx.get(f"{MOCK_SERVER_URL}/reports", timeout=5.0)
        reports = response.json()

        assert len(reports) > 0, "No reports received by mock server"
        last_report = reports[-1]

        # Basic validation of the forwarded report
        # Note: The actual content depends on how the gateway translates the protobuf
        # For this test, we just ensure *something* valid reached the server
        logger.info(f"Received report: {last_report}")
        assert (
            "id" in last_report or "geometry" in last_report
        )  # Typical GeoJSON or CalTopo format features

    except Exception as e:
        pytest.fail(f"Verification failed: {e}")
