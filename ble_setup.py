import bluetooth
import struct
import machine
from bluetooth import BLE
from config import DEVICE_NAME, save_config
import ujson

CHAR_UUIDS = {
    "wifi_ssid":  bluetooth.UUID("b05758b3-...2ce"),
    "wifi_pwd":   bluetooth.UUID("b05758b3-...2cf"),
    "mqtt_ip":    bluetooth.UUID("b05758b3-...2d0"),
}
SERVICE_UUID = bluetooth.UUID("b05758b3-...2cd")

def advertise_payload(name):
    payload = bytearray()
    payload.extend(struct.pack("BB", len(name) + 1, 0x09))
    payload.extend(name.encode("utf-8"))
    return payload

def run_ble_setup():
    ble = bluetooth.BLE()
    ble.active(True)
    received_data = {}
    chars = {}

    def on_write(event, data):
        if event != 3:
            return
        handle = data[1]
        value = data[2].decode()

        for key, (_, h) in chars.items():
            if handle == h:
                received_data[key] = value
                print(f"{key} received: {value}")
                break

        if len(received_data) == len(CHAR_UUIDS):
            print("All data received. Saving config and rebooting...")
            ble.gap_advertise(None)
            save_config(received_data)
            machine.reset()

    service = [(uuid, bluetooth.FLAG_WRITE) for uuid in CHAR_UUIDS.values()]
    ((handles,),) = ble.gatts_register_services([(SERVICE_UUID, service)])
    chars = {name: (uuid, handle) for name, (uuid, handle) in zip(CHAR_UUIDS.keys(), handles)}

    for _, handle in chars.values():
        ble.gatts_set_buffer(handle, 100)

    ble.irq(handler=on_write)
    ble.gap_advertise(100_000, adv_data=advertise_payload(DEVICE_NAME))
    print(f"BLE advertising as {DEVICE_NAME}...")
