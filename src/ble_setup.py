import asyncio
import aioble
import bluetooth
import machine

from config import DEVICE_NAME, save_config

class BLEConfigurator:
    """
    BLEConfigurator handles Bluetooth Low Energy configuration exchange.
    
    It advertises a GATT service with writable characteristics, waits for values
    to be written (e.g., WiFi SSID, password, MQTT broker IP), and stores them 
    using `save_config()`. After receiving all values, it reboots the device.
    """

    # UUIDs for service and characteristics (custom 16-bit UUIDs recommended)
    SERVICE_UUID = bluetooth.UUID(0xFFB0)
    CHAR_UUIDS = {
        "wifi_ssid": bluetooth.UUID(0xFFB1),
        "wifi_pwd":  bluetooth.UUID(0xFFB2),
        "mqtt_ip":   bluetooth.UUID(0xFFB3),
        # Add more fields here if needed (no code change required elsewhere)
    }

    def __init__(self):
        """
        Initialize the BLE configurator.

        Args:
            device_name (str): The BLE advertisement name for this device.
        """
        self.received = {}

        # Create GATT service
        self.service = aioble.Service(self.SERVICE_UUID)

        # Create a dict of characteristics with write support
        self.chars = {
            key: aioble.Characteristic(self.service, uuid, write=True)
            for key, uuid in self.CHAR_UUIDS.items()
        }
        
        # Register service after defining characteristics
        aioble.register_services(self.service)

    async def wait_for_write(self, char: aioble.Characteristic, key: str):
        """
        Waits for a write event on a given characteristic and stores the result.

        Args:
            char (aioble.Characteristic): The characteristic to monitor.
            key (str): The key to associate with the received value.
        """
        await char.written()  # Wait for a client to write
        value = char.read()   # Read the written value
        value_str = value.decode().strip()
        print(f"[BLE] {key} received: {value_str}")
        self.received[key] = value_str

    async def run(self):
        """
        Starts BLE advertisement, waits for writes to all defined characteristics,
        saves the config, and reboots the device.
        """
        print("[BLE] Starting BLE setup...")

        try:
            async with await aioble.advertise(
                150_000,
                timeout_ms=60_000,
                name=DEVICE_NAME,
                services=[self.SERVICE_UUID]
            ) as conn:

                print(f"[BLE] Advertising as '{DEVICE_NAME}', waiting for data...")

                # Dynamically build write tasks for all characteristics
                tasks = [
                    self.wait_for_write(char, key)
                    for key, char in self.chars.items()
                ]

                await asyncio.gather(*tasks)

                print("[BLE] All data received. Saving config...")
                save_config(self.received)

                print("[BLE] Disconnecting...")
                await conn.disconnect()

        except asyncio.TimeoutError:
            print("[BLE] No connection. Timeout.")

        print("[BLE] Waiting before reboot...")
        await asyncio.sleep(1.0)
        machine.reset()
