# test_mqtt_handler.py

import pytest
import ubinascii
import ujson

from mqtt_handler import MQTTHandler, RelayController, handle_ota_update

# --- Mock Classes ---


class MockPin:
    def __init__(self, pin, mode):
        self.pin = pin
        self.mode = mode
        self._value = None

    def value(self, val=None):
        if val is not None:
            self._value = val
        return self._value


class MockMQTTClient:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload):
        self.published.append((topic, payload))


# --- Fixtures ---


@pytest.fixture
def relay_ctrl():
    ctrl = RelayController()
    ctrl.relay_pins = {
        "relay1": MockPin(16, "OUT"),
        "relay2": MockPin(17, "OUT"),
    }
    return ctrl


@pytest.fixture
def mqtt_handler(relay_ctrl):
    handler = MQTTHandler("test_id", "127.0.0.1", relay_ctrl)
    handler.client = MockMQTTClient()  # inject mock
    return handler


# --- Tests ---


def test_relay_command_sets_correct_pins(mqtt_handler, relay_ctrl):
    """
    Test that a relay command sets the correct relay pin values.
    """
    data = {"relay1": 1, "relay2": 0}
    msg = ujson.dumps(data)
    mqtt_handler._callback(b"devices/test_id/relay", msg)
    assert relay_ctrl.relay_pins["relay1"]._value == 1
    assert relay_ctrl.relay_pins["relay2"]._value == 0


def test_handle_ota_update_writes_files_and_publishes_success(tmp_path, monkeypatch):
    """
    Test that handle_ota_update writes all files and publishes 'success' on completion.
    """
    test_file_content = b'print("Hello, world!")'
    payload = [
        {
            "filename": "main.py",
            "content": ubinascii.b2a_base64(test_file_content).decode().strip(),
        },
        {
            "filename": "config.py",
            "content": ubinascii.b2a_base64(b"config = True").decode().strip(),
        },
    ]
    msg = ujson.dumps(payload)

    monkeypatch.setattr("builtins.open", lambda f, m: (tmp_path / f).open(m))
    monkeypatch.setattr("time.sleep", lambda x: None)
    monkeypatch.setattr("machine.reset", lambda: None)

    client = MockMQTTClient()
    handle_ota_update(msg, mqtt_client=client)

    with (tmp_path / "main.py").open("rb") as f:
        assert f.read() == test_file_content
    with (tmp_path / "config.py").open("rb") as f:
        assert f.read() == b"config = True"

    assert any(
        topic.endswith("ota_status") and payload == b"success"
        for topic, payload in client.published
    )


def test_handle_ota_update_failure_publishes_fail(monkeypatch):
    """
    Test that handle_ota_update publishes 'fail' if something goes wrong.
    """
    bad_msg = "not a json array"
    client = MockMQTTClient()

    monkeypatch.setattr("machine.reset", lambda: None)
    monkeypatch.setattr("time.sleep", lambda x: None)

    handle_ota_update(bad_msg, mqtt_client=client)

    assert any(
        topic.endswith("ota_status") and payload == b"fail"
        for topic, payload in client.published
    )
