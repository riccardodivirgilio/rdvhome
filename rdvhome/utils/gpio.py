# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.keystore import KeyStore

try:
    import RPi.GPIO as GPIO

    print('[GPIO] importing RPi.GPIO, setting BCM mode')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    print('[GPIO] mode set:', GPIO.getmode())

except ImportError:
    GPIO = None
    print('[GPIO] RPi.GPIO not available, using debug mode')


class RaspberryGPIO(object):

    is_debug = False
    GPIO = GPIO

    def __init__(self):
        self.configured_pins = set()
        self._last_input = {}

    async def setup_input(self, n, callback=None, **opts):
        print('[GPIO] setup_input pin=%s' % n)
        if n in self.configured_pins:
            print('[GPIO] setup_input pin=%s already configured, skipping' % n)
            return
        try:
            self.GPIO.setup(n, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
            self.configured_pins.add(n)
            print('[GPIO] setup_input pin=%s OK' % n)
        except Exception as e:
            print('[GPIO] setup_input pin=%s ERROR: %s' % (n, e))
            raise

        if callback:
            self.GPIO.remove_event_detect(n)
            self.GPIO.add_event_detect(n, self.GPIO.RISING, callback=callback, **opts)

    async def setup_output(self, n):
        print('[GPIO] setup_output pin=%s' % n)
        if n in self.configured_pins:
            print('[GPIO] setup_output pin=%s already configured, skipping' % n)
            return
        try:
            self.GPIO.setup(n, self.GPIO.OUT, initial=self.GPIO.HIGH)
            self.GPIO.output(n, self.GPIO.HIGH)
            self.configured_pins.add(n)
            print('[GPIO] setup_output pin=%s OK' % n)
        except Exception as e:
            print('[GPIO] setup_output pin=%s ERROR: %s' % (n, e))
            raise

    async def input(self, n):
        try:
            val = self.GPIO.input(n)
            if self._last_input.get(n) != val:
                print('[GPIO] input pin=%s changed to %s' % (n, val))
                self._last_input[n] = val
            return val
        except Exception as e:
            print('[GPIO] input pin=%s ERROR: %s' % (n, e))
            raise

    async def output(self, n, high=True):
        print('[GPIO] output pin=%s high=%s' % (n, high))
        try:
            self.GPIO.output(n, high and self.GPIO.HIGH or self.GPIO.LOW)
            print('[GPIO] output pin=%s OK' % n)
        except Exception as e:
            print('[GPIO] output pin=%s ERROR: %s' % (n, e))
            raise


class DebugGPIO(object):

    is_debug = True
    GPIO = GPIO

    def __init__(self, path=None):

        self.store = KeyStore(prefix="gpio")
        self.configured_pins = set()

    async def setup_input(self, n, **opts):
        if n in self.configured_pins:
            return
        self.configured_pins.add(n)
        if await self.store.get(n) is None:
            await self.store.set(n, 1)

    async def setup_output(self, n):
        if n in self.configured_pins:
            return
        self.configured_pins.add(n)
        await self.store.set(n, None)

    async def input(self, n):
        return await self.store.get(n)

    async def output(self, n, high=True):
        await self.store.set(n, high and 1 or 0)


def has_gpio():
    return bool(GPIO)


_gpio_singleton = None


def get_gpio():
    global _gpio_singleton
    if _gpio_singleton is None:
        _gpio_singleton = RaspberryGPIO() if has_gpio() else DebugGPIO()
    return _gpio_singleton
