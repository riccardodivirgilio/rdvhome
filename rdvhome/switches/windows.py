# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from pyhap.const import CATEGORY_LIGHTBULB
from rdvhome.utils.async import run_all, wait_all
from rdvhome.switches.base import capabilities, HomekitSwitch, Switch
from rdvhome.utils import json
from rdvhome.utils.colors import color_to_homekit, color_to_philips, homekit_to_color, philips_to_color, to_color
from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import to_data
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.keystore import KeyStore

import aiohttp
import asyncio
import time


class Window(Switch):

    homekit_class = None

    default_capabilities = capabilities(direction = True)

    def __init__(self, id, gpio_up, gpio_down, **opts):

        self.gpio_up   = gpio_up
        self.gpio_down = gpio_down

        self.up   = False
        self.down = False

        self._gpio = None
        self._current_action = None

        super().__init__(id, **opts)

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        await self._gpio.setup_output(self.gpio_up)
        await self._gpio.setup_output(self.gpio_down)

        return self._gpio

    async def status(self):
        return await self.send(up = self.up, down = self.down)

    async def switch(self, direction = None):

        gpio = await self.setup_gpio()

        if not direction:
            self.up = self.down = False

            await gpio.output(self.gpio_up,   high = True)
            await gpio.output(self.gpio_down, high = True)

        elif not getattr(self, direction, False):

            if self._current_action:
                self._current_action.cancel()

            self.up = self.down = False

            if direction == 'up':
                to_activate   = self.gpio_up
                to_deactivate = self.gpio_down
            elif direction == 'down':
                to_activate   = self.gpio_down
                to_deactivate = self.gpio_up
            else:
                raise ValueError('Wrong direction %s' % direction)  

            setattr(self, direction, True) 

            self._current_action = run_all(self.perform_window_action(direction, to_activate, to_deactivate))

        return await self.send(up = self.up, down = self.down)

    async def perform_window_action(self, direction, to_activate, to_deactivate):

        gpio = await self.setup_gpio()

        await gpio.output(to_deactivate, high = True)
        await gpio.output(to_activate,   high = False)

        await asyncio.sleep(direction == 'down' and 12 or 13)

        await gpio.output(to_activate, high = True)
        setattr(self, direction, False) 

        await self.send(up = self.up, down = self.down)