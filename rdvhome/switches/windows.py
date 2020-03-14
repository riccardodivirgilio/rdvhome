# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio

from rpy.functions.asyncio import run_all

from rdvhome.switches.base import Switch, capabilities
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.keystore import KeyStore
import uuid

from rdvhome.conf import settings


class Window(Switch):

    homekit_class = None

    default_capabilities = capabilities(direction=True)

    timing_up = settings.DEBUG and 3 or 13
    timing_down = settings.DEBUG and 3 or 12

    def __init__(self, id, gpio_power, gpio_direction, **opts):

        self.gpio_power = gpio_power
        self.gpio_direction = gpio_direction

        self._gpio = None

        self.store = KeyStore(prefix = 'window')

        super().__init__(id, **opts)

    async def start(self):
        #on start we make sure gpio is all off
        await self.switch()

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        await self._gpio.setup_output(self.gpio_power)
        await self._gpio.setup_output(self.gpio_direction)

        return self._gpio

    async def direction(self):

        gpio = await self.setup_gpio()

        power_off = await gpio.input(self.gpio_power)
        going_up = await gpio.input(self.gpio_direction)

        return {
            'up': bool(not power_off and going_up),
            'down': bool(not power_off and not going_up),
        }

    async def status(self):
        return await self.send(** await self.direction())

    async def switch(self, direction=None):

        gpio = await self.setup_gpio()

        if not direction:

            await gpio.output(self.gpio_power, high=True)
            await gpio.output(self.gpio_direction, high=True)

            return await self.status()

        status = await self.direction()

        if not status[direction]:

            id = str(uuid.uuid4())

            await self.store.set(self.id, id)

            gpio = await self.setup_gpio()

            await gpio.output(self.gpio_direction, high=direction == "up")
            await gpio.output(self.gpio_power, high=False)

            run_all(self.stop_window(direction, id))

        return await self.status()

    async def stop_window(self, direction, id):

        await asyncio.sleep(direction == "up" and self.timing_up or self.timing_down)

        if id == await self.store.get(self.id, id):
            gpio = await self.setup_gpio()

            await gpio.output(self.gpio_power, high=True)
            await gpio.output(self.gpio_direction, high=True)

            return await self.status()
