# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio

from rpy.functions.asyncio import run_all

from rdvhome.switches.base import Switch, capabilities
from rdvhome.utils.gpio import get_gpio


class Window(Switch):

    homekit_class = None

    default_capabilities = capabilities(direction=True)

    def __init__(self, id, gpio_power, gpio_direction, **opts):

        self.gpio_power = gpio_power
        self.gpio_direction = gpio_direction

        self.up = False
        self.down = False

        self._gpio = None
        self._current_action = None

        super().__init__(id, **opts)

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        await self._gpio.setup_output(self.gpio_power)
        await self._gpio.setup_output(self.gpio_direction)

        return self._gpio

    async def status(self):
        return await self.send(up=self.up, down=self.down)

    async def switch(self, direction=None):

        gpio = await self.setup_gpio()

        if not direction:
            self.up = self.down = False

            await gpio.output(self.gpio_power, high=True)
            await gpio.output(self.gpio_direction, high=True)

        elif not getattr(self, direction, False):

            if self._current_action:
                self._current_action.cancel()

            self.up = self.down = False

            setattr(self, direction, True)

            self._current_action = run_all(
                self.perform_window_action(direction)
            )

        return await self.send(up=self.up, down=self.down)

    async def perform_window_action(self, direction):

        gpio = await self.setup_gpio()

        await gpio.output(self.gpio_power, high=False)
        await gpio.output(self.gpio_direction, high=direction == "up")

        await asyncio.sleep(direction == "down" and 12 or 13)

        await gpio.output(self.gpio_power, high=True)
        await gpio.output(self.gpio_direction, high=True)

        setattr(self, direction, False)

        await self.send(up=self.up, down=self.down)
