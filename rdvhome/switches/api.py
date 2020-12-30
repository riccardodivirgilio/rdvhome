# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import time
import traceback

import aiohttp
from pyhap.const import CATEGORY_LIGHTBULB
from rpy.functions.datastructures import data
from functools import cache
from rdvhome.switches import switches
from rdvhome.switches.base import HomekitSwitch, Switch, capabilities
from rdvhome.utils import json
from rdvhome.utils.colors import (
    HSB, color_to_homekit, color_to_philips, homekit_to_color,
    philips_to_color, to_color
)
from collections import defaultdict
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.keystore import KeyStore




class RemoteControl(Switch):

    default_capabilities = capabilities(visible=False)

    pooling_interval = 0

    def __init__(self, ipaddress=None, access_token=None, **opts):

        self.ipaddress = ipaddress
        self.access_token = access_token

        super().__init__(**opts)

    async def api_request(self, path="", payload=None):

        path = self.get_api_url(path)

        async with aiohttp.ClientSession() as session:
            if payload:
                async with session.put(path, json=payload) as response:
                    return await response.json(loads=json.loads, content_type=None)
            else:
                async with session.get(path) as response:
                    return await response.json(loads=json.loads, content_type=None)

    def get_api_url(self, path):
        raise NotImplementedError

    async def switch_direction(self, switch, direction, **credentials):
        pass

    async def switch_power(self, switch, on, **credentials):
        pass

    async def switch_color(self, switch, color, **credentials):
        pass

    async def watch(self):

        if not self.pooling_interval:
            return

        while True:
            await self.status()
            await asyncio.sleep(self.pooling_interval)

    def get_supported_switches(self):
        for l in switches:
            try:
                v = l.credentials[self.id]

                if v is not None:
                    yield l, v
            except (KeyError, AttributeError):
                pass

class PhilipsControl(RemoteControl):

    def get_api_url(self, path):
        return "http://%s/api/%s/lights/%s" % (self.ipaddress, self.access_token, path)

    async def switch_power(self, switch, on, **credentials):
        await switch.assign_state(on = on)

    async def switch_color(self, switch, color, **credentials):
        await switch.assign_state(**to_color(color).serialize())

class NanoleafControl(RemoteControl):

    def get_api_url(self, path):
        raise NotImplementedError

class GPIOControl(RemoteControl):

    pooling_interval = 1

    @property
    @cache
    def gpio_registry(self):

        registry = defaultdict(set)

        for switch, credentials in self.get_supported_switches():

            for v in credentials.values():
                registry[v].add(switch)

        return registry

    def get_api_url(self, path):
        return "http://%s:8080%s" % (self.ipaddress, path)

    async def switch_direction(self, switch, direction, gpio_power, gpio_direction, **credentials):
        pass

    async def switch_power(self, switch, on, gpio_status, gpio_relay, **credentials):
        await switch.assign_state(on = on)

    async def status(self):
        pins = await self.api_request('/status/')
        for p, is_high in pins.input.items():
            for switch in self.gpio_registry.get(int(p), ()):
                await switch.assign_state(on = not is_high)
        


        

