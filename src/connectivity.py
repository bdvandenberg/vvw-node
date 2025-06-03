import network
import time

def connect_wifi(ssid, password, attempts=20, interval=0.5):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    print("Connecting to WiFi...")
    wlan.connect(ssid, password)
    for _ in range(attempts):
        if wlan.isconnected():
            break
        time.sleep(interval)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("Connected to WiFi:", ip)
        return ip
    else:
        print("Failed to connect to WiFi.")
        wlan.active(False)
        return None
