# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.toggles.base import Toggle, ToggleList

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

IN  = 1
OUT = 0

if GPIO:
    GPIO.setmode(GPIO.BOARD)
else:
    from django.core.cache import cache

def get_input(pin):
    if GPIO:
        return bool(GPIO.input(pin))
    else:
        return cache.get('gpio-state-%s' % pin, False)

def set_output(pin, mode):
    if GPIO:
        return bool(GPIO.output(pin, mode))
    else:
        cache.set('gpio-state-%s' % pin, mode)
        return bool(mode)

def setup_pin(pin = None, mode = IN):
    if GPIO and pin:
        GPIO.setup(pin, mode)

class RaspberryToggle(Toggle):

    def __init__(self, id, toggle_gpio, status_gpio = None, **opts)

        self.toggle_gpio = toggle_gpio
        self.status_gpio = status_gpio or toggle_gpio

        gpio.setup_pin(self.status_gpio, gpio.IN)
        gpio.setup_pin(self.toggle_gpio, gpio.OUT)

        super(RaspberryToggle, self).__init__(id, **opts)

class RaspberryToggleList(ToggleList):

    def __init__(self, server, toggles = ()):
        self.server  = server

        super(RaspberryToggleList, self).__init__(toggles)

local_toggles = ToggleList(
    RASPBERRY, (
        RaspberryToggle('s1', toggle_gpio = 1, name = "Salone 1", alias = ['s']),
        RaspberryToggle('s2', toggle_gpio = 2, name = "Salone 2", alias = ['s']),
        RaspberryToggle('b1', toggle_gpio = 3, name = "Bagno 1",  alias = ['b']),
        RaspberryToggle('b2', toggle_gpio = 4, name = "Bagno 2",  alias = ['b']),
    )
)