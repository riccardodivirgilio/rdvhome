# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from pyhap.const import CATEGORY_LIGHTBULB

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

        self.direction = None

        super().__init__(id, **opts)

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        await self._gpio.setup_output(self.gpio_up)
        await self._gpio.setup_output(self.gpio_down)

        return self._gpio

    async def status(self):
        return await self.send(direction = self.direction)

    async def switch(self, direction = None):
        print('WINDOW', self, direction)