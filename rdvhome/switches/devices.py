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

class Device(Switch):

    def __init__(self, id, gpioserver = None, nanoleaf = None, philips = None, **opts):

        self.credentials = data(gpioserver = gpioserver, nanoleaf = nanoleaf, philips = philips)

        super().__init__(id, **opts)

    def collect_api_call(self, on = None, color = None, direction = None):
        for target, credentials in self.credentials.items():
            if credentials is not None:
                for controller in switches.filter(target):
                    if direction is not None:
                        yield controller.switch_direction(self, direction, **credentials)

                    if color is not None:
                        yield controller.switch_color(self, color, **credentials)

                    if on is not None:
                        yield controller.switch_power(self, on, **credentials)

    async def switch(self, **opts):

        coros = self.collect_api_call(**opts)

        return await wait_all(coros)



