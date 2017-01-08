# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.utils import six

from rdvhome import gpio
from rdvhome.server import RASPBERRY

import socket

class Toggle(object):

    def __init__(self, server, toggle_gpio, status_gpio = None, name = None):
        self.server = server
        self.toggle_gpio = toggle_gpio
        self.status_gpio = status_gpio or toggle_gpio
        self.name = name

        if self.is_local():
            gpio.setup_pin(self.status_gpio, gpio.IN)
            gpio.setup_pin(self.toggle_gpio, gpio.OUT)

    def id(self):
        return '%s-%.2i' % (self.server.id(), self.toggle_gpio)

    def serialize(self):
        return {
            'server': self.server.name,
            'name': self.name,
            'status': self.get_status()
        }

    def is_local(self):
        if settings.DEBUG:
            return True
        return socket.gethostname() == self.server.id()

    def switch(self, status = None):
        if status is None:
            status = not self.get_status()
        return self.set_status(status)

    def get_status(self):
        return gpio.get_input(self.status_gpio)

    def set_status(self, status = True):
        return gpio.set_output(self.toggle_gpio, status)

class ToggleList(object):

    def __init__(self, *servers):
        self.servers = servers

    def serialize(self):
        return OrderedDict(
            (toggle.id(), toggle.serialize())
            for toggle in self
        )

    def get(self, pk):
        for obj in self:
            if obj.id() == pk:
                return obj

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.__class__(*filter(lambda toggle: toggle.id() == func, self))
        return self.__class__(*filter(func, self))

    def switch(self, *args, **kw):
        return [toggle.switch(*args, **kw) for toggle in self]

    def __bool__(self):
        return bool(self.servers)

    def __len__(self):
        return len(self.servers)

    def __iter__(self):
        return iter(self.servers)

all_toggles = ToggleList(
    Toggle(server = RASPBERRY, toggle_gpio = 1, name = "Test light"),
    Toggle(server = RASPBERRY, toggle_gpio = 2, name = "Test light"),
)

local_toggles = all_toggles.filter(lambda toggle: toggle.is_local())