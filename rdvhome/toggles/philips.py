# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.server import PHILIPS
from rdvhome.toggles.base import Toggle, ToggleList
from rdvhome.utils.requests import fetch_all

import urllib.request

class PhilipsToggle(Toggle):

    def __init__(self, id, philips_id, **opts):
        self.philips_id = philips_id
        super(PhilipsToggle, self).__init__(id, **opts)

class PhilipsToggleList(ToggleList):

    def __init__(self, server, *args, **opts):
        self.server = server
        super(PhilipsToggleList, self).__init__(*args, **opts)

    def copy(self, *args, **opts):
        return self.__class__(self.server, *args, **opts)

    def full_url(self, url):
        return 'http://%s/api/%s%s' % (
            self.server.ipaddress,
            self.server.user,
            url
        )

    def get_status(self):

        results = fetch_all((
            self.full_url('/lights/%s' % toggle.philips_id)
            for toggle in self
        ))

        return {
            toggle: {
                key: result['state'][key]
                for key in ('on', 'bri', 'hue', 'sat')
            }
            for result, toggle in zip(results, self)
        }

    def switch(self, status = None):

        results = fetch_all((
            lambda session: session.put(
                self.full_url('/lights/%s/state' % toggle.philips_id),
                json = {"on": bool(status)}
            )
            for toggle in self
        ))

        return {
            toggle: bool(status)
            for result, toggle in zip(results, self)
        }

toggles_list = PhilipsToggleList(
    PHILIPS, (
        PhilipsToggle('led1', philips_id = 1),
    )
)