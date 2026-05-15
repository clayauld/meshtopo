import base64
from unittest.mock import Mock

import meshtastic.protobuf.mesh_pb2 as mesh_pb2
import meshtastic.protobuf.mqtt_pb2 as mqtt_pb2
import meshtastic.protobuf.portnums_pb2 as portnums_pb2
import meshtastic.protobuf.telemetry_pb2 as telemetry_pb2
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config.config import Config, CryptoConfig
from gateway_app import DEFAULT_LONGFAST_KEY, GatewayApp


@pytest.fixture
def mock_config():
    config = Mock(spec=Config)
    config.crypto = CryptoConfig()
    return config


@pytest.fixture
def gateway_app(mock_config):
    app = GatewayApp(mock_config)
    app.logger = Mock()
    app.config = mock_config
    app._process_telemetry_message = Mock()
    app._get_tenant_node_configs = Mock(return_value=[])
    return app


@pytest.mark.asyncio
async def test_protobuf_decryption(gateway_app):
    # Setup test encrypted payload
    tel = telemetry_pb2.Telemetry()
    tel.time = 123456
    tel.device_metrics.battery_level = 90
    payload_bytes = tel.SerializeToString()

    packet_id = 9999
    from_node = 123
    nonce = (
        packet_id.to_bytes(4, "little") + from_node.to_bytes(4, "little") + b"\x00" * 8
    )

    key_bytes = base64.b64decode(DEFAULT_LONGFAST_KEY)

    packet = mesh_pb2.MeshPacket()
    packet.id = packet_id
    setattr(packet, "from", from_node)

    envelope = mqtt_pb2.ServiceEnvelope()
    envelope.packet.CopyFrom(packet)

    data = {
        "_is_protobuf": True,
        "_mqtt_retain": False,
    }

    data_msg = mesh_pb2.Data()
    data_msg.portnum = portnums_pb2.TELEMETRY_APP
    data_msg.payload = payload_bytes
    data_bytes = data_msg.SerializeToString()

    # Now encrypt data_bytes
    cipher = Cipher(
        algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_bytes = encryptor.update(data_bytes) + encryptor.finalize()

    packet.encrypted = encrypted_bytes
    envelope.packet.CopyFrom(packet)
    data["payload_bytes"] = envelope.SerializeToString()

    await gateway_app._process_message(data, "msh/US/2/e/LongFast/123")

    # Check that it routed to telemetry handler
    gateway_app._process_telemetry_message.assert_called_once()
    args, kwargs = gateway_app._process_telemetry_message.call_args
    assert args[0]["type"] == "telemetry"
    assert args[0]["payload"]["battery_level"] == 90
    assert args[1] == "123"
