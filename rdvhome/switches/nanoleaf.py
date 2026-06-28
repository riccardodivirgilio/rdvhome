# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import aiohttp

from rpy.functions.datastructures import data

from rdvhome.switches.base import capabilities
from rdvhome.switches.philips import RemoteBase, debounce, remove_none
from rdvhome.utils import json
from rdvhome.utils.colors import (
    HSB, color_to_homekit, color_to_nanoleaf, color_to_philips, color_to_homekit,
    homekit_to_color, philips_to_color, to_color
)


class NanoleafControl(RemoteBase):

    def __init__(self, id, effects=None, **opts):
        self.effects = data(effects or {})
        super().__init__(id, **opts)

    @property
    def default_capabilities(self):
        return capabilities(
            on=True,
            hue=True,
            saturation=True,
            brightness=True,
            effects=self.effects,
        )

    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)

    async def api_request(self, path="", payload=None):
        # Nanoleaf answers writes with an empty 204 body (and an empty 400 for
        # an unknown effect), so parse the response only when there is one.
        url = self.get_api_url(path)

        async with aiohttp.ClientSession() as session:
            method = session.put(url, json=payload) if payload else session.get(url)
            async with method as response:
                text = await response.text()
                return json.loads(text) if text.strip() else data()

    @debounce(1)
    async def get_nanoleaf_status(self):
        state = await self.api_request('/state')
        effect = await self.api_request('/effects/select')

        return data(
            on=state.on.value,
            allow_on=True,
            hue=state.hue.value / state.hue.max,
            brightness=state.brightness.value / state.brightness.max,
            saturation=state.sat.value / state.sat.max,
            effect=effect if effect in self.effects else None,
        )

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
                # Scenes broadcast the same effect to every nanoleaf, but each
                # device exposes a different set, so ignore one we don't have.
                if self.effects and effect not in self.effects:
                    return await self.send()

                await self.api_request('/effects', payload = {'select': effect})
                return await self.send(on = True, color = color, effect = effect)

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
                return await self.send(effect = None, on = True, color = effect)

        defaults = dict(self._get_state_changes(on, color))

        await self.api_request('/state', payload = defaults)

        # Setting colour/power leaves the device in solid mode: clear any
        # previously selected effect so the UI stops highlighting it.
        return await self.send(effect = None, **remove_none(on=on, color = color))

    async def is_on(self):
        return (await self.get_nanoleaf_status()).on
