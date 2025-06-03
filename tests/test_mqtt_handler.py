import pytest
import ubinascii
import ujson

from mqtt_handler import handle_ota_update, mqtt_callback

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
def relay_pins():
    # Provide a relay dict that mimics the real one
    return {
        "relay1": MockPin(16, "OUT"),
        "relay2": MockPin(17, "OUT"),
    }

@pytest.fixture
def mqtt_client():
    return MockMQTTClient()

# --- Tests ---

def test_relay_command_sets_correct_pins(monkeypatch, relay_pins):
    """
    Test that a relay command sets the correct relay pin values.
    """
    from mqtt_handler import mqtt_callback

    # Patch the global RELAY_PINS used by mqtt_handler
    monkeypatch.setattr("mqtt_handler.RELAY_PINS", relay_pins)
    # Valid relay control message
    data = {"relay1": 1, "relay2": 0}
    msg = ujson.dumps(data)
    # The topic must end with b"/relay"
    mqtt_callback(b"devices/xxx/relay", msg)
    assert relay_pins["relay1"]._value == 1
    assert relay_pins["relay2"]._value == 0

def test_handle_ota_update_writes_files_and_publishes_success(tmp_path, monkeypatch):
    """
    Test that handle_ota_update writes all files and publishes 'success' on completion.
    """
    from mqtt_handler import handle_ota_update

    # Prepare test OTA payload
    test_file_content = b'print("Hello, world!")'
    payload = [
        {"filename": "main.py", "content": ubinascii.b2a_base64(test_file_content).decode().strip()},
        {"filename": "config.py", "content": ubinascii.b2a_base64(b"config = True").decode().strip()}
    ]
    msg = ujson.dumps(payload)

    # Patch open() to write to a tmp_path, and patch time.sleep and machine.reset
    monkeypatch.setattr("builtins.open", lambda filename, mode: (tmp_path / filename).open(mode))
    monkeypatch.setattr("time.sleep", lambda x: None)
    monkeypatch.setattr("machine.reset", lambda: None)

    client = MockMQTTClient()
    handle_ota_update(msg, mqtt_client=client)

    # Check that files were written
    with (tmp_path / "main.py").open("rb") as f:
        assert f.read() == test_file_content
    with (tmp_path / "config.py").open("rb") as f:
        assert f.read() == b"config = True"

    # Check that a success status was published
    assert any(topic.endswith("ota_status") and payload == b"success" for topic, payload in client.published)

def test_handle_ota_update_failure_publishes_fail(monkeypatch):
    """
    Test that handle_ota_update publishes 'fail' if something goes wrong.
    """
    from mqtt_handler import handle_ota_update

    # Malformed payload triggers exception
    bad_msg = "not a json array"
    client = MockMQTTClient()

    # Patch machine.reset and time.sleep so they don't do anything
    monkeypatch.setattr("machine.reset", lambda: None)
    monkeypatch.setattr("time.sleep", lambda x: None)

    handle_ota_update(bad_msg, mqtt_client=client)

    # Check that a fail status was published
    assert any(topic.endswith("ota_status") and payload == b"fail" for topic, payload in client.published)
