# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.functions.datastructures import data

from rdvhome.switches.base import capabilities
from rdvhome.switches.philips import RemoteBase, debounce, remove_none
from rdvhome.utils.colors import (
    HSB, color_to_homekit, color_to_nanoleaf, color_to_philips, color_to_homekit,
    homekit_to_color, philips_to_color, to_color
)
from rdvhome.switches import switches
from rdvhome.switches.base import HomekitSwitch, Switch, capabilities
from rpy.functions.asyncio import syncronous_wait_all, wait_all
from rpy.functions.datastructures import data

class Provider(object):

    def __init__(self, id = None, **credentials):
        self.id = id
        self.credentials = credentials

    @property
    def control(self):
        return switches.get(self.id)

    async def switch_on(self, switch, **opts):
        if self.control:
            return await self.control.switch_on(switch = switch, **opts, **self.credentials)

    async def switch_color(self, switch, **opts):
        if self.control:
            return await self.control.switch_color(switch = switch, **opts, **self.credentials)

    async def switch_direction(self, switch, **opts):
        if self.control:
            return await self.control.switch_direction(switch = switch, **opts, **self.credentials)


class Device(Switch):

    @property
    def default_capabilities(self):
        return capabilities(
            on=bool(self.providers.on),
            hue=bool(self.providers.color),
            saturation=bool(self.providers.color),
            brightness=bool(self.providers.color),
            direction=bool(self.providers.direction),
        )

    def __init__(self, id, color = {}, on = {}, direction = {}, **opts):

        self.providers = data(
            color = Provider(**color),
            on = Provider(**on),
            direction = Provider(**direction),
        )

        super().__init__(id, **opts)

    async def switch(self, on = None, color = None, direction = None):

        await self.providers.on.switch_on(self, on = on)
        await self.providers.color.switch_color(self, color = color)
        await self.providers.direction.switch_direction(self, direction = direction)


    def get_control_with_credentials(self, name):
        opts = self.providers[name]
        return switches.get(opts.id), opts



