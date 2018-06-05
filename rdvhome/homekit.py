# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

from rdvhome.switches import switches

import asyncio
import logging

"""An example of how to setup and start an Accessory.
This is:
1. Create the Accessory object you want.
2. Add it to an AccessoryDriver, which will advertise it on the local network,
    setup a server to answer client queries, etc.
"""

logging.basicConfig(level=logging.INFO)

class LightBulb(Accessory):

    category = CATEGORY_LIGHTBULB

    @classmethod
    def _gpio_setup(_cls, pin):
        return
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT)

    def __init__(self, *args, pin=11, **kwargs):
        super().__init__(*args, **kwargs)

        serv_light = self.add_preload_service('Lightbulb')
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_bulb)

        self.pin = pin
        self._gpio_setup(pin)

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._gpio_setup(self.pin)

    #@Accessory.run_at_interval(1)
    #def run(self):
    #    self.char_on.set_value(random.randint(0, 1))

    def set_bulb(self, value):

        print(value)

        return

        if value:
            GPIO.output(self.pin, GPIO.HIGH)
        else:
            GPIO.output(self.pin, GPIO.LOW)

    def stop(self):
        super().stop()
        #GPIO.cleanup()

def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Bridge')

    for switch in switches:
        bridge.add_accessory(LightBulb(driver, switch.name, aid = switch.id))

    return bridge

# Start the accessory on port 51826
driver = AccessoryDriver(
    port = 51826, 
    loop = asyncio.get_event_loop(),
)

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory = get_bridge(driver))