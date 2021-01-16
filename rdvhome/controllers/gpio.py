from collections import defaultdict

from rdvhome.controllers.base import Controller as BaseController

import aiohttp

from rpy.functions.decorators import to_data
from rpy.functions.datastructures import data

@to_data
def make_power_state(state):

    yield "allow_on", bool(state)
    if state:
        yield "on", not bool(state.gpio_status)

@to_data
def make_direction_state(state):

    yield "allow_direction", bool(state)
    if state:

        power_off = state.gpio_power
        going_up = state.gpio_direction

        if power_off:
            yield "up", False
            yield "down", False
        elif bool(not power_off and going_up):
            yield "up", True
            yield "down", False
        else:
            yield "up", False
            yield "down", True


class Controller(BaseController):
    def get_api_url(self, path="/"):
        return "http://%s:8080%s" % (self.ipaddress, path)

    async def get_current_state(self):
        try:
            state = await self.api_request("/status/")
        except aiohttp.ClientConnectionError:
            state = None

        result = defaultdict(dict)

        for func, mapping in (
            (make_power_state, self.power),
            (make_direction_state, self.direction),
            ):

            for id, opts in mapping.items():
                result[id].update(
                    func(
                        state and data((name, state.input[value]) for name, value in opts.items()) or None
                    )
                )

        for w in self.direction.keys():
            print(w, result[w])

        return result

    def generate_power_path(self, switches):

        mapping = self.get_value_for_property("power", "gpio_relay")

        for s in switches:
            yield "low"
            yield mapping[s.id]

        yield "wait"
        yield "25"

        for s in switches:
            yield "high"
            yield mapping[s.id]

    async def switch_power(self, switches, power):
        await self.api_request("/%s/" % "/".join(self.generate_power_path(switches)))
        await super().switch_power(switches, power)