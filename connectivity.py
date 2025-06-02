import network
import time

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    if wlan.isconnected():
        print("Connected to WiFi:", wlan.ifconfig()[0])
        return True
    else:
        print("Failed to connect to WiFi.")
        return False
