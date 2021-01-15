
from rdvhome.controllers.base import Controller as BaseController


class Controller(BaseController):

    def get_api_url(self, path="/"):
        return "http://%s/api/%s/lights%s" % (self.ipaddress, self.access_token, path)