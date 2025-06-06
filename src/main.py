import os
import time
import sys

import machine
import traceback

from ble_setup import run_ble_setup
from config import CONFIG_PATH, load_config
from led_status import LedStatus
from mqtt_handler import run_normal_mode

FATAL_LOG_PATH = "fatal_error.log"

led = LedStatus()  # Onboard LED status handler

def main():
    if CONFIG_PATH in os.listdir():
        print("[CONFIG] Config file found.")
        config = load_config()
        if config:
            print("[CONFIG] Config loaded. Starting normal mode.")
            led.set("on")
            run_normal_mode(config)
        else:
            print("[CONFIG] Invalid config. Entering BLE setup.")
            led.set("fast")
            run_ble_setup()
    else:
        print("[CONFIG] No config found. Running BLE setup immediately (dev mode).")
        led.set("fast")
        run_ble_setup()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Write traceback to a file before resetting
        try:
            with open(FATAL_LOG_PATH, "w") as f:
                f.write("FATAL ERROR:\n")
                f.write(str(e) + "\n\n")
                f.write("Traceback:\n")
                traceback.print_exc(file=f)
        except Exception as log_err:
            # If even logging fails, print to stdout
            print("Failed to write fatal error log:", log_err)

        print("[FATAL ERROR]", e)
        traceback.print_exc(file=sys.stdout)
        led.set("fast")
        time.sleep(5)
        machine.reset()


