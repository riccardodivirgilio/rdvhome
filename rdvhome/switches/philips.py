# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch
from rdvhome.utils.colors import hsb_to_hsl

import aiohttp

class PhilipsSwitch(Switch):

    def __init__(self, id, philips_id, ipaddress, username, **opts):
        self.philips_id = philips_id
        self.ipaddress  = ipaddress
        self.username   = username
        super(PhilipsSwitch, self).__init__(id, **opts)

    def api_url(self, extra = ''):
        return 'http://%s/api/%s/lights/%s%s' % (
            self.ipaddress,
            self.username,
            self.philips_id,
            extra
        )

    async def status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url()) as response:
                r = await response.json()
                return self.send(
                    on = r['state']['on'],
                    color = hsb_to_hsl(
                        float(r['state']['hue']) / 65534,
                        float(r['state']['sat']) / 254,
                        float(r['state']['bri']) / 254
                    ),
                    brightness = float(r['state']['bri']) / 254
                )

    async def switch(self, on = False):
        async with aiohttp.ClientSession() as session:
            async with session.put(self.api_url('/state'), json = {"on": bool(on)}) as response:
                r = await response.json()
                return self.send(on = bool(on))