# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

class Device(object):

    def __init__(self, id, ipaddress, name = None, user = None, default_password = "raspberry"):
        self.ipaddress = ipaddress
        self.name = name
        self.default_password = default_password
        self.user = user
        self.id = id

    def host(self):
        return "%s@%s:22" % (self.user, self.name)

RASPBERRY = Device(
    id = 'rasp',
    name = "rdvpi.local",
    user = "pi",
    ipaddress = "192.168.1.200",
    )

NAS = Device(
    id = 'nas',
    name = "rdvnas.local",
    user = 'server',
    ipaddress = "192.168.1.230",
    )

PHILIPS = Device(
    id = 'phil',
    user = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
    ipaddress = "192.168.1.179",
    )

DEVICES = [RASPBERRY]