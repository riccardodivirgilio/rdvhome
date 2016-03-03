# -*- coding: utf-8 -*-

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

IN  = 1
OUT = 0

PINS = {
    10: OUT,
    12: IN,
    18: OUT,
}

if GPIO:
    GPIO.setmode(GPIO.BOARD)
    for n, mode in PINS.items():
        GPIO.setup(n, mode)