import dht
import machine

DHT_PIN = 15

def read_dht():
    sensor = dht.DHT22(machine.Pin(DHT_PIN))
    try:
        sensor.measure()
        return {
            "temp": sensor.temperature(),
            "humidity": sensor.humidity()
        }
    except Exception as e:
        print("DHT read error:", e)
        return None
