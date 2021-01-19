from collections import defaultdict

from rdvhome.controllers.base import Controller as BaseController

import aiohttp
from rdvhome.conf import settings
import asyncio
from rpy.functions.decorators import to_data, decorate
from rpy.functions.datastructures import data
from rdvhome.state import switches

import uuid

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

    timings = {"up": 13, "down": 12}

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
                
        return result

    @decorate(lambda s: "/%s/" % "/".join(s))
    def generate_power_path(self, switches, power):
        for s in switches:
            if not s.on == power:
                yield "low"
                yield self.power[s.id].gpio_relay

        yield "wait"
        yield "25"

        for s in switches:
            if not s.on == power:
                yield "high"
                yield self.power[s.id].gpio_relay

    @decorate(lambda s: "/%s/" % "/".join(s))
    def generate_direction_path(self, switches, direction):        
        for s in switches:
            if direction == "stop":
                yield "high"
                yield self.direction[s.id].gpio_power
                yield "high"
                yield self.direction[s.id].gpio_direction
            elif direction in ("up", "down"):
                yield "low"
                yield self.direction[s.id].gpio_power
                yield direction == "up" and "high" or "low"
                yield self.direction[s.id].gpio_direction
            else:
                raise NotImplementedError('direction %s not implemented' % direction)

    async def switch_power(self, switches, power):
        await self.api_request(self.generate_power_path(switches, power))
        await super().switch_power(switches, power)

    async def switch_direction(self, switches, direction):
        await self.api_request(self.generate_direction_path(switches, direction))
        self._sender = sender = uuid.uuid4()
        await super().switch_direction(switches, direction)

        if direction in self.timings:
            await asyncio.sleep(self.timings[direction])
            if self._sender == sender:
                await self.switch_direction(switches, "stop")

    async def ensure_window_off(self, i, switch, counters):
        for direction, moving in (("up", switch.up), ("down", switch.down)):
            if moving:
                counters[direction] += 1
            else:
                counters[direction] = 0

            if counters[direction] >= self.timings[direction]:
                await self.switch_direction((switch, ), "stop")
                counters[direction] = 0

    async def watch(self):
        for id in self.direction.keys():
            await self.create_periodic_task(
                self.ensure_window_off, switch = switches.get(id), interval = 1, counters = {"up": 0, "down": 0}
            )

        await super().watch()
