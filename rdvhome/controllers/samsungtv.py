from rdvhome.controllers.base import Controller as BaseController

import aiohttp

class Controller(BaseController):
    def get_api_url(self, path="/"):
        return "http://%s:8001/api/v2%s" % (self.ipaddress, path)

    async def get_current_state(self):
        try:
            state = await self.api_request("/")
        except aiohttp.ClientConnectionError:
            state = None

        return {key: dict(on=bool(state), allow_on=False) for key in self.power.keys()}