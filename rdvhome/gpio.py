# -*- coding: utf-8 -*-

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

IN  = 1
OUT = 0

PINS = {
	3:  OUT,
	5:  OUT,
	7:  OUT,
	8:  OUT,
	10: OUT,
	11: OUT,
	12: OUT,
	13: OUT,
	15: OUT,
	16: OUT,
	18: OUT,
	19: OUT,
	21: OUT,
	22: OUT,
	23: OUT,
	24: OUT,
	26: OUT,
}

if GPIO:
    GPIO.setmode(GPIO.BOARD)
    for n, mode in PINS.items():
        GPIO.setup(n, mode)
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