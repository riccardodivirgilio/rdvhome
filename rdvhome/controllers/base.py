
from rdvhome.switches.base import BaseSwitchList

class Controller(object):

    def __init__(self, id, **opts):
        self.id = id


class ControllerList(BaseSwitchList):
    pass