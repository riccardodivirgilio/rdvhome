
from rdvhome.controllers.base import Controller as BaseController

class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:8080%s" % (self.ipaddress, path)

    async def get_current_state(self):
        data = await self.api_request('/status/')
        mapping = self.get_value_for_property('power', 'gpio_status')
        return {
            key: {
                'allow_on': True,
                'on': not bool(data.input[value])
            } 
            for key, value in mapping.items()
        }
