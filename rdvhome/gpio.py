# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.server import RASPBERRY

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

IN  = 1
OUT = 0

if GPIO:
    GPIO.setmode(GPIO.BOARD)
    for n, data in RASPBERRY.gpio.items():
        GPIO.setup(n, data.get("mode", OUT))
else:
    STORE = {}

def get_input(pin):
    if GPIO:
        return bool(GPIO.input(pin))
    else:
        return STORE.get(pin, False)

def set_output(pin, mode):
    if GPIO:
        return bool(GPIO.output(pin, mode))
    else:
        STORE[pin] = bool(mode)
        return STORE[pin]