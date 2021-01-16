
from rdvhome.switches.events import EventStream
import aiohttp
from rdvhome.utils import json
from rdvhome.state import switches, controllers
from rpy.functions.asyncio import run_all, wait_all

class AbstractController(EventStream):

    def __init__(self, id, power_control = {}, color_control = {}, direction_control = {}, **opts):
        self.id = id
        self.power = power_control
        self.color = color_control
        self.direction = direction_control

    def filter_switches_for(self, switches, command):
        return switches.filter(
            tuple(getattr(self, command).keys())
        )

    async def switch(self, switches, command, value):
        print('%s switching %s for %s to %s' % (self.id, command, switches, value))
        return await getattr(self, 'switch_%s' % command)(switches, value)

    async def switch_power(self, switches, power):
        pass

    async def switch_direction(self, switches, direction):
        pass

    async def switch_color(self, switches, color):
        pass

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.id)

class Controller(AbstractController):

    interval = 5

    def __init__(self, ipaddress, access_token = None, **opts):
        super().__init__(**opts)

        self.ipaddress = ipaddress
        self.access_token = access_token

    def get_value_for_property(self, command, prop):
        return {id: info[prop]   for id, info in getattr(self, command).items()}

    def get_api_url(self, path="/"):
        raise NotImplementedError

    async def api_request(self, path="/", payload=None):

        path = self.get_api_url(path)

        async with aiohttp.ClientSession() as session:
            if payload:
                async with session.put(path, json=payload) as response:
                    return await response.json(loads=json.loads, content_type=None)
            else:
                async with session.get(path) as response:
                    return await response.json(loads=json.loads, content_type=None)

    async def get_current_state(self):
        return 

    async def periodic_task(self):
        state = await self.get_current_state()
        if state:
            await wait_all(
                switches.get(key).update(**value)
                for key, value in state.items()
            )