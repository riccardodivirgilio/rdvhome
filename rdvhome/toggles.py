# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import defaultdict, OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.baseconv import base64 as encoder

from rdvhome import gpio
from rdvhome.server import RASPBERRY

import socket

class Toggle(object):

    def __init__(self, id, server, toggle_gpio, status_gpio = None, name = None, alias = []):
        self.id = id
        self.server = server
        self.toggle_gpio = toggle_gpio
        self.status_gpio = status_gpio or toggle_gpio
        self.name = name
        self.alias = alias
        self.order = encoder.decode(id)

        if self.is_local():
            gpio.setup_pin(self.status_gpio, gpio.IN)
            gpio.setup_pin(self.toggle_gpio, gpio.OUT)

    def serialize(self):
        on = self.get_status()
        return dict(
            on = on,
            name = self.name,
            order = self.order,
            action = reverse('toggle', kwargs = {'mode': not on, 'number': self.id}),
        )

    def is_local(self):
        if settings.DEBUG:
            return True
        return socket.gethostname() == self.server.id

    def switch(self, status = None):
        if status is None:
            status = not self.get_status()
        return self.set_status(status)

    def get_status(self):
        return gpio.get_input(self.status_gpio)

    def set_status(self, status = True):
        return gpio.set_output(self.toggle_gpio, status)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class ToggleList(object):

    def __init__(self, *servers):
        self.servers = list(servers)

    def serialize(self):
        return OrderedDict(
            (toggle.id, toggle.serialize())
            for toggle in self
        )

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.__class__(*filter(lambda toggle: toggle.id == func, self))
        if isinstance(func, (list, tuple, dict)):
            return self.__class__(*filter(lambda toggle: toggle.id in func, self))
        return self.__class__(*filter(func, self))

    def switch(self, *args, **kw):
        return [toggle.switch(*args, **kw) for toggle in self]

    def register(self, other):
        self.servers.append(other)
        return self

    def __bool__(self):
        return bool(self.servers)

    def __len__(self):
        return len(self.servers)

    def __iter__(self):
        return iter(self.servers)

    def __repr__(self):
        return repr(self.servers)

local_toggles = ToggleList(
    Toggle('s1', server = RASPBERRY, toggle_gpio = 1, name = "Salone 1", alias = ['s']),
    Toggle('s2', server = RASPBERRY, toggle_gpio = 2, name = "Salone 2", alias = ['s']),
    Toggle('b1', server = RASPBERRY, toggle_gpio = 3, name = "Bagno 1",  alias = ['b']),
    Toggle('b2', server = RASPBERRY, toggle_gpio = 4, name = "Bagno 2",  alias = ['b']),
)

local_toggles = local_toggles.filter(lambda toggle: toggle.is_local())

toggle_registry = defaultdict(ToggleList)
for toggle in local_toggles:
    toggle_registry[toggle.id].register(toggle)
    toggle_registry['all'].register(toggle)
    for name in toggle.alias:
        toggle_registry[name].register(toggle)