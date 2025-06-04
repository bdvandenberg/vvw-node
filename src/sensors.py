import dht
import machine

DHT_PIN = 15
_sensor = dht.DHT22(machine.Pin(DHT_PIN))


def read_dht():
    try:
        _sensor.measure()
        return {"temp": _sensor.temperature(), "humidity": _sensor.humidity()}
    except Exception as e:
        print("DHT read error:", e)
        return None
