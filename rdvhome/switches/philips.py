# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch
import aiohttp
from rdvhome.utils.datastructures import data

class PhilipsSwitch(Switch):

    def __init__(self, id, philips_id, ipaddress, username, **opts):
        self.philips_id = philips_id
        self.ipaddress  = ipaddress
        self.username   = username
        super(PhilipsSwitch, self).__init__(id, **opts)

    def api_url(self):
        return 'http://%s/api/%s/lights/%s' % (
            self.ipaddress,
            self.username,
            self.philips_id
        )

    async def get_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url()) as response:
                r = await response.json()
                return data(on = r['state']['on'])