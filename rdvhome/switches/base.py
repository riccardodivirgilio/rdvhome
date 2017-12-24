# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from operator import methodcaller

from rdvhome.events import status_stream
from rdvhome.utils.async import wait_all
from rdvhome.utils.datastructures import data
from rdvhome.utils.functional import first, iterate

import asyncio
import six

class Switch(object):

    def __init__(self, id, name = None, alias = ()):
        self.id = id
        self.name = name
        self.alias = frozenset(iterate(self.id, alias, 'all'))

    def send(self, on, **opts):

        event = data(
            id     = self.id,
            name   = self.name,
            action = '/switch/%s/%s' % (self.id, on and 'off' or 'on'),
            alias  = self.alias,
            on     = on,
            off    = not on,
            **opts
        )

        status_stream.send(event)

        return event

    async def switch(self, mode = None):
        raise NotImplementedError

    async def status(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class SwitchList(object):

    def __init__(self, switches):
        if isinstance(switches, (tuple, list, set, frozenset)):
            self.switches = switches
        else:
            self.switches = tuple(iterate(switches))

    async def status(self, *args, **opts):
        return {
            serialized.id: serialized
            for serialized in await wait_all(obj.status(*args, **opts) for obj in self)
        }

    async def switch(self, *args, **opts):
        return {
            serialized.id: serialized
            for serialized in await wait_all(obj.switch(*args, **opts) for obj in self)
        }

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda switch: func in switch.alias, self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(filter(lambda switch: any(f in switch.alias for f in func), self))
        if isinstance(func, Switch):
            return self.copy([func])
        if func:
            return self.copy(filter(func, self))
        return self

    def __bool__(self):
        return bool(self.switches)

    def __len__(self):
        return len(self.switches)

    def __iter__(self):
        return iter(self.switches)

    def __repr__(self):
        return repr(self.switches)