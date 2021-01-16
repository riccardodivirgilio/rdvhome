
from rdvhome.controllers.base import Controller as BaseController
import aiohttp

class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:8080%s" % (self.ipaddress, path)

    async def get_current_state(self):
        try:
            data = await self.api_request('/status/')
        except aiohttp.ClientConnectionError:
            data = None
        
        mapping = self.get_value_for_property('power', 'gpio_status')
        return {
            id: {
                'allow_on': bool(data),
                'on': bool(data and not bool(data.input[key]))
            } 
            for id, key in mapping.items()
        }

    def generate_power_path(self, switches):

        mapping = self.get_value_for_property('power', 'gpio_relay')

        for s in switches:
            yield 'low'
            yield mapping[s.id]

        yield 'wait'
        yield '25'

        for s in switches:
            yield 'high'
            yield mapping[s.id]

    async def switch_power(self, switches, power):
        await self.api_request('/%s/' % "/".join(self.generate_power_path(switches)))
        await super().switch_power(switches, power)