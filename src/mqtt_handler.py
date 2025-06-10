# mqtt_handler.py

import time
import machine
import ujson
from umqtt.simple import MQTTClient

from connectivity import connect_wifi
from ota import handle_ota_update
from sensors import read_dht


class RelayController:
    """
    Handles GPIO relay control.
    """
    def __init__(self):
        self.relay_pins = {
            "relay1": machine.Pin(16, machine.Pin.OUT),
            "relay2": machine.Pin(17, machine.Pin.OUT),
        }
        self.set_all(False)

    def set_all(self, state: bool):
        for pin in self.relay_pins.values():
            pin.value(1 if state else 0)

    def update_from_dict(self, data: dict):
        for name, state in data.items():
            if name in self.relay_pins:
                self.relay_pins[name].value(1 if state else 0)
                print(f"[RELAY] {name} -> {'ON' if state else 'OFF'}")


class MQTTHandler:
    """
    Manages MQTT connection and communication.
    """
    def __init__(self, client_id: str, broker_ip: str, relay_ctrl: RelayController):
        self.client = MQTTClient(client_id, broker_ip)
        self.client.set_callback(self._callback)
        self.client_id = client_id
        self.relay_ctrl = relay_ctrl

    def _callback(self, topic, msg):
        print(f"[MQTT] {topic} = {msg}")
        try:
            if topic.endswith(b"/relay"):
                self.relay_ctrl.update_from_dict(ujson.loads(msg))
            elif topic.endswith(b"/ota"):
                print("[MQTT] OTA update requested")
                handle_ota_update(msg, mqtt_client=self.client)
        except Exception as e:
            print(f"[MQTT] Callback error: {e}")

    def connect(self):
        self.client.connect()
        self.client.subscribe(f"devices/{self.client_id}/relay")
        self.client.subscribe(f"devices/{self.client_id}/ota")
        self.client.publish(f"devices/{self.client_id}/status", b"online")

    def check_msg(self):
        self.client.check_msg()

    def publish_sensor_data(self, data):
        topic = f"devices/{self.client_id}/sensors"
        self.client.publish(topic, ujson.dumps(data))

    def disconnect(self):
        self.client.disconnect()


class NodeApp:
    """
    Represents the Pico Node main application logic.
    """
    def __init__(self, config: dict):
        self.config = config
        self.relay_ctrl = RelayController()
        self.mqtt = MQTTHandler(config["device_id"], config["mqtt_ip"], self.relay_ctrl)

    def run(self):
        self.relay_ctrl.set_all(False)

        if not connect_wifi(self.config["wifi_ssid"], self.config["wifi_pwd"]):
            print("[WIFI] Connection failed")
            return

        self.mqtt.connect()

        try:
            last_pub = time.ticks_ms()
            while True:
                self.mqtt.check_msg()
                if time.ticks_diff(time.ticks_ms(), last_pub) > 5000:
                    data = read_dht()
                    if data:
                        self.mqtt.publish_sensor_data(data)
                    last_pub = time.ticks_ms()
                time.sleep(0.1)
        finally:
            self.mqtt.disconnect()
