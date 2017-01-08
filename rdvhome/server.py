# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

class Device(object):

    def __init__(self, id, ipaddress, name, user = "pi", default_password = "raspberry", gpio = {}):
        self.ipaddress = ipaddress
        self.name = name
        self.default_password = default_password
        self.gpio = gpio
        self.user = user
        self.id = id

    def host(self):
        return "%s@%s:22" % (self.user, self.name)

RASPBERRY = Device(
    ipaddress = "192.168.1.200",
    name = "rdvpi.local",
    id = 'a'
    )

NAS = Device(
    ipaddress = "192.168.1.230",
    name = "rdvnas.local",
    id = 'b'
    )

DEVICES = [RASPBERRY]