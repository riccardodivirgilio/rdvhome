
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

    async def switch_power(self, switches, power):
        mapping = self.get_value_for_property('power', 'gpio_power')
        await wait_all(
            self.api_request(path="/%s/state" % mapping[switch.id], payload=dict(on = bool(power)))
            for switch in switches
        )

