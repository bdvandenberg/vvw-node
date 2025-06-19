# mypy: disable-error-code=attr-defined

"""
conftest.py — Pytest MicroPython compatibility shims.

Mocks all MicroPython-specific modules for desktop testing.
"""

import base64
import binascii
import json as std_json
import sys
import types

# -------------------------
# Mock Classes & Functions
# -------------------------


# --- DHT Sensor ---
class MockDHT22:
    def __init__(self, pin):
        self.pin = pin
        self._temperature = 25.0
        self._humidity = 50.0

    def measure(self):
        pass

    def temperature(self):
        return self._temperature

    def humidity(self):
        return self._humidity


# --- WLAN (network) ---
class MockWLAN:
    STA_IF = "STA_IF"
    AP_IF = "AP_IF"

    def __init__(self, mode):
        self.mode = mode
        self.active_state = False
        self.connected = False
        self._ifconfig = ("192.168.1.100", "255.255.255.0", "192.168.1.1", "8.8.8.8")

    def active(self, state=None):
        if state is not None:
            self.active_state = state
        return self.active_state

    def isconnected(self):
        return self.connected

    def connect(self, ssid, password):
        self.connected = True

    def ifconfig(self):
        return self._ifconfig


# --- MQTT Client ---
class MockMQTTClient:
    def __init__(self, *args, **kwargs):
        self.subscriptions = []
        self.published = []
        self.callback = None

    def set_callback(self, cb):
        self.callback = cb

    def connect(self):
        pass

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def publish(self, topic, payload):
        self.published.append((topic, payload))

    def check_msg(self):
        pass

    def disconnect(self):
        pass


# --- Pin (machine) ---
class MockPin:
    OUT = "OUT"
    IN = "IN"
    PULL_UP = "PULL_UP"

    def __init__(self, pin, mode=None, pull=None):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self._value = 0

    def value(self, val=None):
        if val is not None:
            self._value = val
        return self._value


def unique_id():
    """Return a fixed device unique ID as bytes."""
    return b"\xaa\xbb\xcc\xdd\xee\xff"


# -------------------------
# Module Registrations
# -------------------------

# DHT module (dht)
mock_dht = types.ModuleType("dht")
mock_dht.DHT22 = MockDHT22
mock_dht.DHT11 = MockDHT22
sys.modules["dht"] = mock_dht

# Network module (network)
mock_network = types.ModuleType("network")
mock_network.WLAN = MockWLAN
mock_network.STA_IF = MockWLAN.STA_IF
mock_network.AP_IF = MockWLAN.AP_IF
sys.modules["network"] = mock_network

# MQTT module (umqtt.simple)
mock_umqtt_simple = types.ModuleType("umqtt.simple")
mock_umqtt_simple.MQTTClient = MockMQTTClient
sys.modules["umqtt.simple"] = mock_umqtt_simple

# Machine module (machine)
mock_machine = types.ModuleType("machine")
mock_machine.Pin = MockPin
mock_machine.reset = lambda: print("[Mock] machine.reset() called")
mock_machine.unique_id = unique_id
sys.modules["machine"] = mock_machine

# ujson → Python stdlib json
sys.modules["ujson"] = std_json

# ubinascii → Python stdlib equivalents
mock_ubinascii = types.ModuleType("ubinascii")
mock_ubinascii.a2b_base64 = base64.b64decode
mock_ubinascii.b2a_base64 = base64.b64encode
mock_ubinascii.hexlify = binascii.hexlify
sys.modules["ubinascii"] = mock_ubinascii
