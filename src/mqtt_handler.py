# mqtt_handler.py

import ujson
import time
import machine
from umqtt.simple import MQTTClient
from connectivity import connect_wifi
from sensors import read_dht
from config import DEVICE_ID
import ubinascii
from ota import handle_ota_update

RELAY_PINS = {
    "relay1": machine.Pin(16, machine.Pin.OUT),
    "relay2": machine.Pin(17, machine.Pin.OUT),
}

client = None

def mqtt_callback(topic, msg):
    """
    Main MQTT callback handler.

    Handles messages for:
    - Relay control on topic 'devices/{DEVICE_ID}/relay'.
    - OTA updates on topic 'devices/{DEVICE_ID}/ota'.
    """
    print(f"[MQTT] {topic} = {msg}")
    if topic.endswith(b"/relay"):
        try:
            data = ujson.loads(msg)
            for name, state in data.items():
                if name in RELAY_PINS:
                    RELAY_PINS[name].value(1 if state else 0)
                    print(f"Set {name} to {'ON' if state else 'OFF'}")
        except Exception as e:
            print("Relay cmd error:", e)
    elif topic.endswith(b"/ota"):
        print("[MQTT] OTA update received")
        handle_ota_update(msg, mqtt_client=client) 

def connect_mqtt(client_id, broker_ip):
    """
    Connects to the MQTT broker and subscribes to relevant topics.

    Subscribes to:
        - 'devices/{client_id}/relay' for relay control.
        - 'devices/{client_id}/ota' for OTA update commands.

    Publishes a status message on 'devices/{client_id}/status' when online.

    Args:
        client_id (str): Unique identifier for the MQTT client (usually the device ID).
        broker_ip (str): IP address or hostname of the MQTT broker.

    Returns:
        MQTTClient: The initialized and connected MQTT client.
    """
    global client
    client = MQTTClient(client_id, broker_ip)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(f"devices/{client_id}/relay")
    client.subscribe(f"devices/{client_id}/ota")
    client.publish(f"devices/{client_id}/status", b"online")
    return client

def run_normal_mode(config):
    """
    Runs the normal device operation mode:
    - Connects to WiFi using credentials from config.
    - Connects to MQTT broker.
    - Periodically reads sensors and publishes data.
    - Listens for MQTT relay control and OTA update commands.

    Args:
        config (dict): Device configuration.

    Returns:
        None
    """
    # Ensure all relays are OFF at startup
    for pin in RELAY_PINS.values():
        pin.value(0)

    if not connect_wifi(config["wifi_ssid"], config["wifi_pwd"]):
        return

    mqtt = connect_mqtt(config["device_id"], config["mqtt_ip"])
    try:
        last_pub = time.ticks_ms()
        while True:
            mqtt.check_msg()
            if time.ticks_diff(time.ticks_ms(), last_pub) > 5000:
                data = read_dht()
                if data:
                    mqtt.publish(f"devices/{DEVICE_ID}/sensors", ujson.dumps(data))
                last_pub = time.ticks_ms()
            time.sleep(0.1)
    finally:
        mqtt.disconnect()
