# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch, SwitchList

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

class RaspberrySwitch(Switch):

    def __init__(self, id, switch_gpio, status_gpio = None, **opts)

        self.switch_gpio = switch_gpio
        self.status_gpio = status_gpio or switch_gpio

        gpio.setup_pin(self.status_gpio, gpio.IN)
        gpio.setup_pin(self.switch_gpio, gpio.OUT)

        super(RaspberrySwitch, self).__init__(id, **opts)

class RaspberrySwitchList(SwitchList):

    def __init__(self, server, switches = ()):
        self.server  = server

        super(RaspberrySwitchList, self).__init__(switches)

local_switches = SwitchList(
    RASPBERRY, (
        RaspberrySwitch('s1', switch_gpio = 1, name = "Salone 1", alias = ['s']),
        RaspberrySwitch('s2', switch_gpio = 2, name = "Salone 2", alias = ['s']),
        RaspberrySwitch('b1', switch_gpio = 3, name = "Bagno 1",  alias = ['b']),
        RaspberrySwitch('b2', switch_gpio = 4, name = "Bagno 2",  alias = ['b']),
    )
)