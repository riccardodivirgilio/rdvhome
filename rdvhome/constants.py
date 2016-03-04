# -*- coding: utf-8 -*-

class Server(object):

    def __init__(self, ipaddress, name, user = "pi", default_password = "raspberry", gpio = {}):
        self.ipaddress = ipaddress
        self.name = name
        self.default_password = default_password
        self.gpio = gpio

    def __unicode__(self):
        return "%s@%s:22" % (self.name, self.name)

RASPBERRY = Server(
    ipaddress = "192.168.1.200",
    name = "rdvpi.local",
    gpio = {
        3:  {},
        5:  {},
        7:  {},
        8:  {},
        10: {},
        11: {},
        12: {"label": "Test led"},
        13: {},
        15: {},
        16: {},
        18: {},
        19: {},
        21: {},
        22: {},
        23: {},
        24: {},
        26: {},
        }
    )