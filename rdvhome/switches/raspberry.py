# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch, capabilities
from rdvhome.utils.colors import color_to_philips, philips_to_color, to_color
from rdvhome.utils.decorators import to_data
from rdvhome.utils.keystore import KeyStore
from rdvhome.utils.gpio import RaspberryGPIO, DebugGPIO

import aiohttp

class RaspberrySwitch(Switch):

    default_capabilities = capabilities(on = True)

    gpio_class = RaspberryGPIO

    def __init__(self, gpio_relay, gpio_status, *args, **opts):

        super().__init__(*args, **opts)

        self.gpio        = self.gpio_class()
        self.gpio_relay  = gpio_relay
        self.gpio_status = gpio_status

        self.gpio.setup_output(self.gpio_relay)
        self.gpio.setup_input(self.gpio_status)

    def raspberry_switch(self, on = True):
        self.gpio.output(self.gpio_relay, high = False)

    def raspberry_status(self):
        return not self.gpio.input(self.gpio_status)

    async def switch(self, on = None, color = None):

        if on is not None:
            if not on == self.raspberry_status():
                self.raspberry_switch(on)
            
        return self.send(on = on, full = False)

    async def status(self):
        return self.send(on = self.raspberry_status())

class RaspberryDebugSwitch(RaspberrySwitch):

    gpio_class = DebugGPIO

    def raspberry_switch(self, on = True):
        super().raspberry_switch(on = on)
        self.gpio.store.set(self.gpio_status, not on and 1 or 0)