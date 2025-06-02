import ujson
import time
import machine
from umqtt.simple import MQTTClient
from connectivity import connect_wifi
from sensors import read_dht
from config import DEVICE_ID

RELAY_PINS = {
    "relay1": 16,
    "relay2": 17,
}

client = None

def mqtt_callback(topic, msg):
    print(f"[MQTT] {topic} = {msg}")
    if topic.endswith(b"/relay"):
        try:
            data = ujson.loads(msg)
            for name, state in data.items():
                if name in RELAY_PINS:
                    pin = machine.Pin(RELAY_PINS[name], machine.Pin.OUT)
                    pin.value(1 if state else 0)
                    print(f"Set {name} to {'ON' if state else 'OFF'}")
        except Exception as e:
            print("Relay cmd error:", e)

def connect_mqtt(client_id, broker_ip):
    global client
    client = MQTTClient(client_id, broker_ip)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(f"devices/{client_id}/relay")
    client.publish(f"devices/{client_id}/status", b"online")
    return client

def run_normal_mode(config):
    for pin in RELAY_PINS.values():
        machine.Pin(pin, machine.Pin.OUT).value(0)

    if not connect_wifi(config["wifi_ssid"], config["wifi_pwd"]):
        return

    mqtt = connect_mqtt(config["device_id"], config["mqtt_ip"])
    try:
        last_pub = 0
        while True:
            mqtt.check_msg()
            if time.ticks_ms() - last_pub > 5000:
                data = read_dht()
                if data:
                    mqtt.publish(f"devices/{DEVICE_ID}/sensors", ujson.dumps(data))
                last_pub = time.ticks_ms()
            time.sleep(0.1)
    finally:
        mqtt.disconnect()
