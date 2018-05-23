# -*- coding: utf-8 -*-

from rdvhome.utils.importutils import module_path
from rdvhome.utils.importutils import import_string

import os
import json

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
        self.path = module_path('rdvhome', 'gpio')
        try:
            os.makedirs(self.path)
        except FileExistsError:
            pass

    def _write(self, n, payload):
        with open(os.path.join(self.path, '%.2i.json' % n), 'w') as f:
            json.dump(payload, f)

    def _read(self, n):
        try:
            with open(os.path.join(self.path, '%.2i.json' % n), 'rb') as f:
                return json.load(f)
        except FileNotFoundError:
            pass

    def setup_input(self, n):
        if self._read(n) is None:
            self._write(n, 1)

    def setup_output(self, n):
        self._write(n, None)

    def input(self, n):
        return self._read(n)

    def output(self, n, high = True):
        self._write(n, high and 1 or 0)

def get_gpio():
    if GPIO:
        return RaspberryGPIO()
    return DebugGPIO()
