# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import capabilities, Switch
from rdvhome.utils.colors import color_to_philips, philips_to_color, to_color
from rdvhome.utils.decorators import to_data
from rdvhome.utils.keystore import KeyStore

import aiohttp

class PhilipsDebugSwitch(Switch):

    store = KeyStore(prefix = 'philips')
    default_settings = {'on': False, "brightness": 1, "hue": 0.5, "saturation": 1}

    default_capabilities = capabilities(
        on         = True,
        hue        = True,
        saturation = True,
        brightness = True,
    )

    @to_data
    def parse_command(self, on = None, color = None):

        if on is not None:
            yield 'on', bool(on)

        if color is not None:
            yield from to_color(color).serialize().items()

    async def switch(self, on = None, color = None):

        payload = dict(
            self.store.get(self.id, self.default_settings),
            **self.parse_command(on, color)
        )
        self.store.set(self.id, payload)

        return self.send(on = on, color = color, full = False)

    async def status(self):
        return self.send(**self.store.get(self.id, self.default_settings))

class PhilipsSwitch(Switch):

    def __init__(self, id, philips_id, ipaddress, username, **opts):
        self.philips_id = philips_id
        self.ipaddress  = ipaddress
        self.username   = username
        super(PhilipsSwitch, self).__init__(id, **opts)

    async def api_request(self, path = '', payload = None):

        path = 'http://%s/api/%s/lights/%s%s' % (
            self.ipaddress,
            self.username,
            self.philips_id,
            path
        )

        async with aiohttp.ClientSession() as session:
            async with session.put(path, json = payload) as response:
                return await response.json()

    @to_data
    def parse_command(self, on = None, color = None):

        if on is not None:
            yield 'on', bool(on)

        if color is not None:
            yield from color_to_philips(color).items()

    async def status(self):
        response = await self.api_request()
        return self.send(
            on = response.state.on,
            color = philips_to_color(
                hue        = float(response.state.hue),
                saturation = float(response.state.sat),
                brightness = float(response.state.bri),
            ),
        )

    async def switch(self, on = None, color = None):
        payload = self.parse_command(on, color)
        if payload:
            await self.api_request('/state', payload) 

        return self.send(on = on, color = color, full = False)