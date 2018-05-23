# -*- coding: utf-8 -*-

from rdvhome.utils.importutils import module_path
from rdvhome.utils.importutils import import_string
from rdvhome.utils.keystore import KeyStore

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

class RaspberryGPIO(object):

    GPIO = GPIO

    def __init__(self):
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)

    def setup_input(self, n):
        self.GPIO.setup(n, self.GPIO.IN, pull_up_down = self.GPIO.PUD_UP)

    def setup_output(self, n):
        self.GPIO.setup(n,  self.GPIO.OUT)
        self.GPIO.output(n, self.GPIO.HIGH)

    def input(self, n):
        return self.GPIO.input(n)

    def output(self, n, high = True):
        self.GPIO.output(n, high and self.GPIO.HIGH or self.GPIO.LOW)

class DebugGPIO(object):

    GPIO = GPIO

    def __init__(self, path = None):

        self.store = KeyStore(
            path or module_path('rdvhome', 'data'),
            prefix = 'gpio'
        )

    def setup_input(self, n):
        if self.store.get(n) is None:
            self.store.set(n, 1)

    def setup_output(self, n):
        self.store.set(n, None)

    def input(self, n):
        return self.store.get(n)

    def output(self, n, high = True):
        self.store.set(n, high and 1 or 0)

def get_gpio():
    if GPIO:
        return RaspberryGPIO()
    return DebugGPIO()
