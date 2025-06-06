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

BUTTON_PIN = 14
DEV_MODE = True  # Set to False for production

button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
led = LedStatus()  # Onboard LED status handler


def button_pressed():
    return button.value() == 0  # active low


def wait_for_button(timeout_ms=5000):
    print("Waiting for button press to enable BLE setup...")
    led.set("slow")  # Slow blink while waiting for user
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        if button_pressed():
            print("Button pressed. Starting BLE setup...")
            led.set("fast")  # Fast blink during BLE setup
            return True
        time.sleep(0.05)
    print("No button press detected.")
    led.set("off")  # Turn off LED if not proceeding to BLE
    return False


def main():
    print("[BOOT] Starting main...")
    if CONFIG_PATH in os.listdir():
        print("[CONFIG] Config file found.")
        config = load_config()
        if config:
            print("[CONFIG] Config loaded. Starting normal mode.")
            led.set("on")  # Solid LED: normal operation
            run_normal_mode(config)
        else:
            print("[CONFIG] Invalid config. Entering BLE setup.")
            led.set("fast")  # Fast blink: config error
            run_ble_setup()
    else:
        print("[CONFIG] No config found. Waiting for button for BLE setup.")
        if wait_for_button():
            print("[BLE] BLE setup authorized.")
            led.set("fast")
            run_ble_setup()
        else:
            print("[BLE] BLE setup not authorized. Reboot with button held.")
            led.set("off")


def main_dev():
    print("[DEV] Starting in development mode...")
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
        if DEV_MODE:
            main_dev()
        else:
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


