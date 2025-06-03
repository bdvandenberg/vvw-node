# ota.py

"""
OTA update handler for Pico W.

Handles multi-file updates by writing all provided files and rebooting the device.
Publishes MQTT status ('success' or 'fail') after OTA operation.
"""

import time

import machine
import ubinascii
import ujson

from config import DEVICE_ID


def handle_ota_update(msg, mqtt_client=None):
    """
    Handles OTA update commands.

    Expects a JSON array of objects as the MQTT message, where each object
    represents a file to update. Each object must contain:
        - 'filename': The name of the file to be written/updated (e.g. 'main.py').
        - 'content': The base64-encoded contents of the file.

    Args:
        msg (bytes or str): The MQTT message payload containing the update data.
        mqtt_client (MQTTClient, optional): The MQTT client for publishing OTA status.

    Returns:
        None
    """
    try:
        files = ujson.loads(msg)
        for entry in files:
            filename = entry['filename']
            content = ubinascii.a2b_base64(entry['content'])
            with open(filename, 'wb') as f:
                f.write(content)
            print(f"[OTA] Updated {filename}")
        print("[OTA] All files updated, rebooting in 1s")
        try:
            # Publish OTA status if MQTT is up
            if mqtt_client:
                mqtt_client.publish(f"devices/{DEVICE_ID}/ota_status", b"success")
        except Exception as e:
            print("[OTA] Failed to publish ota_status:", e)
        time.sleep(1)
        machine.reset()
    except Exception as e:
        print("[OTA] Error handling update:", e)
        if mqtt_client:
            try:
                mqtt_client.publish(f"devices/{DEVICE_ID}/ota_status", b"fail")
            except Exception as e2:
                print("[OTA] Failed to publish ota_status on failure:", e2)
