import sys
import types
import json as std_json
import base64
import sys
import types
import binascii


class MockDHT22:
    def __init__(self, pin):
        self.pin = pin
        self._temperature = 25.0  # Default mock value
        self._humidity = 50.0     # Default mock value
    def measure(self):
        pass  # In real tests, you could have this change internal state
    def temperature(self):
        return self._temperature
    def humidity(self):
        return self._humidity


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
        self.connected = True  # Simulate success
    def ifconfig(self):
        return self._ifconfig


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


class MockPin:
    OUT = "OUT"
    IN = "IN"
    PULL_UP = "PULL_UP"
    def __init__(self, pin, mode=None, pull=None):
        self.pin = pin
        self.mode = mode
        self._value = 0
    def value(self, val=None):
        if val is not None:
            self._value = val
        return self._value
    
def unique_id():
    # Return a fixed bytes object (as MicroPython does)
    return b'\xaa\xbb\xcc\xdd\xee\xff'
    

mock_dht = types.SimpleNamespace(
    DHT22=MockDHT22,
    DHT11=MockDHT22,
)
sys.modules['dht'] = mock_dht

mock_network = types.SimpleNamespace(
    WLAN=MockWLAN,
    STA_IF=MockWLAN.STA_IF,
    AP_IF=MockWLAN.AP_IF,
)
sys.modules['network'] = mock_network
    
mock_umqtt_simple = types.SimpleNamespace(
    MQTTClient=MockMQTTClient,
)
sys.modules['umqtt.simple'] = mock_umqtt_simple

mock_machine = types.SimpleNamespace(
    Pin=MockPin,
    reset=lambda: print("[Mock] machine.reset() called"),
    unique_id=unique_id,
)
sys.modules["machine"] = mock_machine

sys.modules['ujson'] = std_json
mock_ubinascii = types.SimpleNamespace(
    a2b_base64=base64.b64decode,
    b2a_base64=base64.b64encode,
    hexlify=binascii.hexlify,
)

sys.modules['ubinascii'] = mock_ubinascii
