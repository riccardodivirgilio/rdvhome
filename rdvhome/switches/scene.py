# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches import switches
from rdvhome.switches.base import Switch
from rdvhome.utils.async import run_all
from rdvhome.utils.colors import to_color
from rdvhome.utils.datastructures import data

import asyncio

class SceneSwitch(Switch):

    kind = 'scene'
    default_aliases = []

    def __init__(self, id, on = False, directives = None, **opts):
        self.on = on
        self.directives = data(directives or {})
        super(SceneSwitch, self).__init__(id = id, **opts)

    async def status(self):
        return self.send(on = self.on)

    async def switch(self, on = None, **opts):
        self.on = bool(on)

        if self.on:
            run_all((
                switches.filter(key).switch(**opts)
                for key, opts in self.directives.items()
                ),
                self.delay_off()
            )

        return self.send(on = self.on)

    async def delay_off(self, timeout = 1):
        await asyncio.sleep(timeout)
        self.on = False
        return self.send(on = self.on)