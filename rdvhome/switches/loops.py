# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches import switches
from rdvhome.switches.base import Switch
from rdvhome.utils.async import run_all, wait_all
from rdvhome.utils.colors import Color, to_color
from rdvhome.utils.datastructures import data

import asyncio
import random

class LoopSwitch(Switch):

    kind = 'loop'
    default_aliases = []

    def __init__(self, id, on = False, filter = None, **opts):
        self.on = on
        self.filter = filter

        self._last_loop = None

        super(LoopSwitch, self).__init__(id = id, **opts)

    async def status(self):
        return self.send(on = self.on)

    async def switch(self, on = None, **opts):

        if on is not None:
            self.on = bool(on)

            if self.on:
                self._last_loop = run_all(
                    self.start_loop(switch)
                    for switch in switches.filter(self.filter)
                )
            elif self._last_loop:
                self._last_loop.cancel()
                self._last_loop = None

        return self.send(on = self.on)

    async def start_loop(self, switch, min_time = 0.2, max_time = 1):
        run_all(switch.switch(on = True))

        while self.on:
            run_all(
                switch.switch(color = Color(
                    red   = random.random(),
                    green = random.random(),
                    blue  = random.random(),
                ))
            )
            await asyncio.sleep(random.random() * (max_time - min_time) + min_time)