# mypy: disable-error-code=import-untyped

import machine
import ubinascii
import ujson

CONFIG_PATH = "config.json"


def get_device_id():
    return ubinascii.hexlify(machine.unique_id()).decode()


DEVICE_ID = get_device_id()
DEVICE_NAME = f"Pico-{DEVICE_ID[-6:]}"


def save_config(data):
    # Load current config, or start fresh if not present or invalid
    try:
        with open(CONFIG_PATH, "r") as f:
            config = ujson.loads(f.read())
    except (OSError, ValueError):
        config = {}

    config["device_id"] = DEVICE_ID  # Always update device_id
    config.update(data)  # Overwrite/add new keys

    with open(CONFIG_PATH, "w") as f:
        f.write(ujson.dumps(config))


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return ujson.loads(f.read())
    except (OSError, ValueError):
        # OSError: file not found; ValueError: invalid JSON
        return None
