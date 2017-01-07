# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.server import RASPBERRY

class Toggle(object):

    def __init__(self, server, toggle_gpio, status_gpio = None, name = None):
        self.server = server
        self.toggle_gpio = toggle_gpio
        self.status_gpio = status_gpio
        self.name = name

    def id(self):
        return '%s-%.2i' % (self.server.id(), self.toggle_gpio)

    def serialize(self):
        return {
            'server': self.server.name,
            'name': self.name,
            'toggle_gpio': self.toggle_gpio
        }

class ToggleList(object):

    def __init__(self, *servers):
        self.servers = servers

    def serialize(self):
        return [obj.serialize() for obj in self]

    def __iter__(self):
        return iter(self.servers)

toggles = ToggleList(
    Toggle(server = RASPBERRY, toggle_gpio = 1, name = "Test light"),
    Toggle(server = RASPBERRY, toggle_gpio = 2, name = "Test light"),
)