# main.py

import os
import sys
import time
import asyncio
import machine
import bluetooth

from config import CONFIG_PATH, load_config
from led_status import LedStatus
from ble_setup import BLEConfigurator
from mqtt_handler import NodeApp 

FATAL_LOG_PATH = "fatal_error.log"


class MainController:
    """
    Entry point for the Pico Node firmware.
    Handles initial setup, BLE configuration, and normal MQTT operation.
    """
    def __init__(self):
        self.led = LedStatus()
        self.device_name = "PicoNode"

    async def run(self):
        """
        Main async method to either launch BLE setup or normal operation based on config presence.
        """
        if CONFIG_PATH in os.listdir():
            print("[CONFIG] Config file found.")
            config = load_config()
            print("[CONFIG] Config loaded. Starting normal mode.")
            self.led.set("on")
            node = NodeApp(config)
            node.run()
        else:
            print("[CONFIG] No config found. Running BLE setup.")
            self.led.set("fast")
            configurator = BLEConfigurator()
            await configurator.run()


def handle_fatal_error(e):
    """
    Handles any uncaught exception by logging and rebooting the device.
    """
    try:
        with open(FATAL_LOG_PATH, "w") as f:
            f.write("FATAL ERROR:\n")
            f.write(str(e) + "\n\n")
            f.write("Traceback:\n")
            sys.print_exception(e, f)
    except Exception as log_err:
        print("Failed to write fatal error log:", log_err)

    print("[FATAL ERROR]", e)
    sys.print_exception(e)
    LedStatus().set("fast")
    time.sleep(5)
    machine.reset()


if __name__ == "__main__":
    bluetooth.BLE().active(True)  # Activate BLE stack early
    controller = MainController()
    try:
        asyncio.run(controller.run())
    except Exception as e:
        handle_fatal_error(e)
