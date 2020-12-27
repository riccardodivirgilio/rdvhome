# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.functions.datastructures import data

from rdvhome.switches.base import capabilities
from rdvhome.switches.philips import RemoteBase, debounce, remove_none
from rdvhome.utils.colors import (
    HSB, color_to_homekit, color_to_nanoleaf, color_to_philips, color_to_homekit,
    homekit_to_color, philips_to_color, to_color
)


class NanoleafControl(RemoteBase):

    @property
    def default_capabilities(self):
        return capabilities(
            on=True,
            hue=True,
            saturation=True,
            brightness=True,
        )

    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)

    @debounce(1)
    async def get_nanoleaf_status(self):
        state = await self.api_request('/state')

        return data(on= state.on.value,allow_on= True, hue= state.hue.value / state.hue.max, brightness= state.brightness.value / state.brightness.max, saturation= state.sat.value / state.sat.max)

    async def status(self):
        defaults = await self.get_nanoleaf_status()
        return await self.send(**defaults)

    def _get_state_changes(self, on, color):

        if on is not None:
            yield "on", {"value": on}

        if color is not None and on is not False:
            for key, value in color_to_nanoleaf(color).items():
                yield key, {"value": value}

    async def switch(self, on=None, color=None, effect = None, **opts):


        if effect:

            if isinstance(effect, str):
                await self.api_request('/effects', payload = {'select': effect})
                return await self.send(color = color)

            else:
                await self.api_request('/effects', payload = {'write': {
                    "command": "display",
                    "animName": "New animation",
                    "animType": "highlight",
                    "colorType": "HSB",
                    "animData": None,
                    "palette": tuple(color_to_homekit(dict(brightness = 1, hue = effect.hue, saturation = effect.saturation / (i+1))) for i in range(3)),
                    "brightnessRange": {
                        "minValue": 50,
                        "maxValue": 100
                    },
                    "transTime": {
                        "minValue": 5,
                        "maxValue": 10
                    },
                    "delayTime": {
                        "minValue": 5,
                        "maxValue": 10
                    },
                    "loop": True
                }})
                return await self.send(color = effect)

        defaults = dict(self._get_state_changes(on, color))

        await self.api_request('/state', payload = defaults)

        return await self.send(**remove_none(on=on, color = color))

    async def is_on(self):
        return (await self.get_nanoleaf_status()).on
