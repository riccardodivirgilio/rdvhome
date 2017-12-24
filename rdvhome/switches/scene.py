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

    def __init__(self, id, on = False, colors = None, **opts):
        self.on = on
        self.colors = data(
            (alias, to_color(color))
            for alias, color in colors.items()
        )
        super(SceneSwitch, self).__init__(id = id, **opts)

    async def status(self):
        return self.send(on = self.on)

    async def switch(self, on = False):
        self.on = bool(on)
        if self.on:
            run_all(
                switches.filter(key).switch(on = True)
                for key, value in self.colors.items()
            )

        return self.send(on = self.on)