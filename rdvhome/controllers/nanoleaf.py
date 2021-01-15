
from rdvhome.controllers.base import Controller as BaseController

from rpy.functions.datastructures import data
from collections import defaultdict

from rpy.functions.decorators import to_data
from collections import defaultdict

def make_power_state(state):

    return dict(
        on= state.on.value,
        allow_on= True, 
    )

def make_color_state(state):

    return dict(
        allow_hue = True,
        allow_brightness = True,
        allow_saturation = True,
        hue= state.hue.value / state.hue.max, 
        brightness= state.brightness.value / state.brightness.max, 
        saturation= state.sat.value / state.sat.max
    )  

class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)

    async def get_current_state(self):
        state = await self.api_request('/state')

        mapping = defaultdict(data)

        for func, keys in (
            (make_power_state, self.power.keys()),
            (make_color_state, self.color.keys())
            ):

            for key in keys:
                mapping[key].update(func(state))

        return mapping