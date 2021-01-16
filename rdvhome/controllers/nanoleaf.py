from collections import defaultdict

from rdvhome.controllers.base import Controller as BaseController
from rdvhome.utils.colors import color_to_nanoleaf

from rpy.functions.datastructures import data
from rpy.functions.decorators import to_data

import aiohttp

@to_data
def make_power_state(state):

    yield "allow_on", bool(state)
    if state:
        yield "on", bool(state.on.value)

@to_data
def make_color_state(state):

    yield "allow_hue", bool(state)
    yield "allow_brightness", bool(state)
    yield "allow_saturation", bool(state)

    if state:
        yield "hue", (state.hue.value / state.hue.max)
        yield "brightness", (state.brightness.value / state.brightness.max)
        yield "saturation", (state.sat.value / state.sat.max)
    

class Controller(BaseController):
    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)

    async def get_current_state(self):

        try:
            state = await self.api_request("/state")
        except aiohttp.ClientConnectionError:
            state = None

        mapping = defaultdict(data)

        for func, keys in (
            (make_power_state, self.power.keys()),
            (make_color_state, self.color.keys()),
        ):
            for key in keys:
                mapping[key].update(func(state))

        return mapping

    async def switch_power(self, switches, power):
        await self.api_request("/state", payload={"on": {"value": bool(power)}})
        await super().switch_power(switches, power)

    async def switch_color(self, switches, color):
        await self.api_request(
            "/state",
            payload={key: {"value": value} for key, value in color_to_nanoleaf(color).items()},
        )
        await super().switch_color(switches, color)