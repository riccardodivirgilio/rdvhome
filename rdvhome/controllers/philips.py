from collections import defaultdict

from rdvhome.controllers.base import Controller as BaseController
from rdvhome.utils.colors import color_to_philips, philips_to_color

from rpy.functions.asyncio import wait_all
from rpy.functions.datastructures import data
from rpy.functions.decorators import to_data

import aiohttp

@to_data
def make_power_state(response):

    yield "on", bool(response and response.state.reachable and response.state.on or False)
    yield "allow_on", bool(response and response.state.reachable)

@to_data
def make_color_state(response):

    allow_hue = response and ("hue" in response.state)

    yield "allow_hue", allow_hue
    yield "allow_saturation", allow_hue
    yield "allow_brightness", allow_hue

    if allow_hue:

        yield from philips_to_color(
            hue=round(response.state.hue, 5),
            saturation=round(response.state.sat, 5),
            brightness=round(response.state.bri, 5),
        ).serialize().items()

class Controller(BaseController):
    def get_api_url(self, path="/"):
        return "http://%s/api/%s/lights%s" % (self.ipaddress, self.access_token, path)

    async def get_current_state(self):

        try:
            payload = await self.api_request(path="/")
        except aiohttp.ClientConnectionError:
            payload = {}

        response = defaultdict(data)

        for func, mapping in (
            (make_power_state, self.get_value_for_property("power", "philips_id")),
            (make_color_state, self.get_value_for_property("color", "philips_id")),
        ):
            for id, philips_id in mapping.items():
                response[id].update(func(payload.get(philips_id, None)))

        return response

    async def switch_power(self, switches, power):
        mapping = self.get_value_for_property("power", "philips_id")
        await wait_all(
            self.api_request(
                path="/%s/state" % mapping[switch.id], payload=dict(on=bool(power))
            )
            for switch in switches
        )
        await super().switch_power(switches, power)

    async def switch_color(self, switches, color):
        mapping = self.get_value_for_property("color", "philips_id")
        await wait_all(
            self.api_request(
                path="/%s/state" % mapping[switch.id], payload=color_to_philips(color)
            )
            for switch in switches
        )
        await super().switch_color(switches, color)