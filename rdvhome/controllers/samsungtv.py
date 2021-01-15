
from rdvhome.controllers.base import Controller as BaseController


class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:8001/api/v2%s" % (self.ipaddress, path)
