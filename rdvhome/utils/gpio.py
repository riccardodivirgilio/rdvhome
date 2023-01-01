# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.keystore import KeyStore

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.cleanup()

except ImportError:
    GPIO = None


class RaspberryGPIO(object):

    is_debug = False
    GPIO = GPIO

    async def setup_input(self, n, callback=None, **opts):
        self.GPIO.setup(n, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

        if callback:
            self.GPIO.remove_event_detect(n)
            self.GPIO.add_event_detect(n, self.GPIO.RISING, callback=callback, **opts)

    async def setup_output(self, n):
        print('setup output', n)
        self.GPIO.setup(n, self.GPIO.OUT)
        self.GPIO.output(n, self.GPIO.HIGH)

    async def input(self, n):
        return self.GPIO.input(n)

    async def output(self, n, high=True):

        print('output', n, high)
        self.GPIO.output(n, high and self.GPIO.HIGH or self.GPIO.LOW)


class DebugGPIO(object):

    is_debug = True
    GPIO = GPIO

    def __init__(self, path=None):

        self.store = KeyStore(prefix="gpio")

    async def setup_input(self, n, **opts):
        if await self.store.get(n) is None:
            await self.store.set(n, 1)

    async def setup_output(self, n):
        await self.store.set(n, None)

    async def input(self, n):
        return await self.store.get(n)

    async def output(self, n, high=True):
        await self.store.set(n, high and 1 or 0)


def has_gpio():
    return bool(GPIO)


def get_gpio():
    if has_gpio():
        return RaspberryGPIO()
    return DebugGPIO()
