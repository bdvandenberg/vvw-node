import struct

import bluetooth
import machine

from config import DEVICE_NAME, save_config

CHAR_UUIDS = {
    "wifi_ssid": bluetooth.UUID("b05758b3-18b2-4c82-b819-19d8ffdf02cd"),
    "wifi_pwd": bluetooth.UUID("b05758b3-18b2-4c82-b819-19d8ffdf02ce"),
    "mqtt_ip": bluetooth.UUID("b05758b3-18b2-4c82-b819-19d8ffdf02cf"),
}
SERVICE_UUID = bluetooth.UUID("b05758b3-18b2-4c82-b819-19d8ffdf02d0")


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
        if event != 3:  # gatts_write
            return
        conn_handle, attr_handle = data
        for key, (_, h) in chars.items():
            if attr_handle == h:
                value = ble.gatts_read(h).decode()
                received_data[key] = value
                print(f"{key} received: {value}")
                break

        if len(received_data) == len(CHAR_UUIDS):
            print("All data received. Saving config and rebooting...")
            try:
                ble.gap_advertise(None)
                save_config(received_data)
            except Exception as e:
                print(f"Error saving config: {e}")
            finally:
                machine.reset()

    service = [(uuid, bluetooth.FLAG_WRITE) for uuid in CHAR_UUIDS.values()]
    # Ensure handles is always a tuple/list
    (handles,) = ble.gatts_register_services([(SERVICE_UUID, service)])
    # handles is now (9, 11, 13)
    chars = {
        name: (uuid, handle)
        for name, uuid, handle in zip(CHAR_UUIDS.keys(), CHAR_UUIDS.values(), handles)
    }



    for _, handle in chars.values():
        ble.gatts_set_buffer(handle, 100)

    ble.irq(on_write)
    ble.gap_advertise(200, adv_data=advertise_payload(DEVICE_NAME))
    print(f"BLE advertising as {DEVICE_NAME}...")
    
    # Block here to keep BLE running until config is saved
    try:
        while True:
            machine.idle()
    except KeyboardInterrupt:
        print("BLE setup interrupted, exiting.")

