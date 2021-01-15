
from rdvhome.controllers.base import Controller as BaseController


class Controller(BaseController):
    
    def get_api_url(self, path="/"):
        return "http://%s:16021/api/v1/%s%s" % (self.ipaddress, self.access_token, path)