# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import random

from rdvhome.switches import switches
from rdvhome.switches.base import Switch, capabilities
from rdvhome.utils.colors import random_color, to_color
from rpy.functions.async import run_all, wait_all
from rpy.functions.functional import is_iterable


class ControlSwitch(Switch):

    kind = 'control'
    default_aliases = []
    default_capabilities = capabilities(on = True)

    def __init__(self, id, on = False, automatic_on = False, automatic_off = True, filter = Switch.kind, colors = lambda switch, i: random_color(), timeout = None, **opts):

        self.on            = on
        self.filter        = filter
        self.colors        = colors
        self.timeout       = timeout
        self.automatic_on  = automatic_on
        self.automatic_off = automatic_off

        self._future_when_on  = None
        self._future_when_off = None

        super().__init__(id = id, **opts)

    async def status(self):
        return await self.send(on = self.on)

    async def switch(self, on = None, **opts):

        if on is None or (on and self.on) or (not on and not self.on):
            return await self.send(on = self.on)

        if self._future_when_on:
            self._future_when_on.cancel()
            self._future_when_on = None

        self.on = bool(on)

        await wait_all(
            self.on and self.automatic_on  and switches.filter(self.automatic_on is True and self.filter or self.automatic_on).switch(on = True) or (),
            self.on and self.automatic_off and switches.filter(
                lambda s: s.kind == self.kind and not s.id == self.id
            ).switch(on = False) or ()
        )

        if self.on:
            self._future_when_on  = run_all(self.when_on())

        return await self.send(on = self.on)

    async def when_on(self):
        run_all((
            self.when_switch_on(switch, i)
            for i, switch in enumerate(switches.filter(self.filter))
            ),
            not self.timeout and self.delay_off() or ()
        )

    async def when_switch_on(self, switch, i):
        if switch.capabilities.allow_hue:
            if await switch.is_on():
                await switch.switch(color = self.assign_color(switch, i))
            t = 0
            if self.timeout:
                while self.on:
                    await asyncio.sleep(
                        self.assign_timeout(switch, i + t)
                    )

                    t += 1

                    if await switch.is_on():
                        await switch.switch(
                            color = to_color(self.assign_color(switch, i + t)),
                        )

    async def delay_off(self, timeout = 0.5):
        await asyncio.sleep(timeout)
        return await self.switch(on = False)

    def assign_timeout(self, switch, i):
        if callable(self.timeout):
            return self.timeout(switch, i)
        elif is_iterable(self.timeout):
            min_time, max_time = self.timeout
            return random.random() * (max_time - min_time) + min_time
        else:
            return self.timeout

    def assign_color(self, switch, i):
        if callable(self.colors):
            return to_color(self.colors(switch, i))
        elif is_iterable(self.colors):
            return self.colors[(i+1) % len(self.colors)]
        else:
            return self.colors
