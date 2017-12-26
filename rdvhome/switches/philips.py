# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch
from rdvhome.utils.colors import color_to_philips, hsb_to_color, hsb_to_hsl, hsl_to_hsb, philips_to_color, to_color
from rdvhome.utils.decorators import decorate, to_data

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
                    color = philips_to_color(
                        hue        = float(r['state']['hue']),
                        saturation = float(r['state']['sat']),
                        brightness = float(r['state']['bri']),
                    ),
                )

    @to_data
    def _parse_command(self, on = None, color = None):

        if on is not None:
            yield 'on', bool(on)

        if color is not None:
            for key, value in color_to_philips(color).items():
                yield key, value

    async def switch(self, on = None, color = None):

        payload = self._parse_command(on, color)

        async with aiohttp.ClientSession() as session:
            async with session.put(self.api_url('/state'), json = payload) as response:
                r = await response.json()
                return self.send(on = on, color = color, full = False)