import _thread
import time

import machine

LED_PIN = 25

class LedStatus:
    def __init__(self, pin=LED_PIN):
        self.led = machine.Pin(pin, machine.Pin.OUT)
        self.mode = "off"
        self._running = True
        _thread.start_new_thread(self._run, ())

    def set(self, mode):
        """Set mode: 'off', 'on', 'slow', 'fast'"""
        self.mode = mode

    def _run(self):
        while self._running:
            if self.mode == "on":
                self.led.value(1)
                time.sleep(0.1)
            elif self.mode == "off":
                self.led.value(0)
                time.sleep(0.1)
            elif self.mode == "slow":
                self.led.value(1)
                time.sleep(0.5)
                self.led.value(0)
                time.sleep(0.5)
            elif self.mode == "fast":
                self.led.value(1)
                time.sleep(0.1)
                self.led.value(0)
                time.sleep(0.1)
            else:
                self.led.value(0)
                time.sleep(0.1)

    def stop(self):
        self._running = False
        self.led.value(0)
