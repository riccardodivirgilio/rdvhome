
from rdvhome.controllers.base import Controller as BaseController
import aiohttp

from rpy.functions.datastructures import data
from collections import defaultdict

from rpy.functions.decorators import to_data
from collections import defaultdict
from rpy.functions.asyncio import run_all, wait_all
from rdvhome.utils.colors import color_to_nanoleaf

def make_power_state(state):

    return dict(
        on= bool(state and state.on.value),
        allow_on= bool(state), 
    )

def make_color_state(state):

    return dict(
        allow_hue = bool(state),
        allow_brightness = bool(state),
        allow_saturation = bool(state),
        hue= state and (state.hue.value / state.hue.max) or 0, 
        brightness= state and (state.brightness.value / state.brightness.max) or 0, 
        saturation= state and (state.sat.value / state.sat.max) or 0
    )  

class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)

    async def get_current_state(self):
        
        try:
            state = await self.api_request('/state')
        except aiohttp.ClientConnectionError:
            state = None

        mapping = defaultdict(data)

        for func, keys in (
            (make_power_state, self.power.keys()),
            (make_color_state, self.color.keys())
            ):
            for key in keys:
                mapping[key].update(func(state))

        return mapping

    async def switch_power(self, switches, power):
        await self.api_request('/state', payload = {"on": {"value": bool(power)}})
        await super().switch_power(switches, power)

    async def switch_color(self, switches, color):
        await self.api_request('/state', payload = {
            key: {"value": value}
            for key, value in color_to_nanoleaf(color).items()
        })
        await super().switch_color(switches, color)