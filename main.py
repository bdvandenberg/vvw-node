import os
from config import CONFIG_PATH, load_config
from ble_setup import run_ble_setup
from mqtt_handler import run_normal_mode

def main():
    if CONFIG_PATH in os.listdir():
        config = load_config()
        run_normal_mode(config)
    else:
        run_ble_setup()

main()
