# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict
import asyncio
import six
from operator import methodcaller
from rdvhome.utils.functional import first, iterate
from rdvhome.utils.async import wait_all

class Switch(object):

    def __init__(self, id, name = None, alias = []):
        self.id = id
        self.name = name
        self._alias = alias

    def alias(self):
        yield self.id
        yield 'all'
        yield from self._alias

    async def serialize(self):
        status = await self.get_status()
        status.update(dict(
            id     = self.id,
            name   = self.name,
            action = '/switch/%s/%s' % (self.id, status['on'] and 'on' or 'off'),
            alias  = self.alias()
        ))
        return status

    async def switch(self, status = None):
        raise NotImplementedError

    async def get_status(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class SwitchList(object):

    def __init__(self, switches):
        if isinstance(switches, (tuple, list, set, frozenset)):
            self.switches = switches
        else:
            self.switches = tuple(iterate(switches))

    async def serialize(self):
        return {
            serialized.id: serialized
            for serialized in await wait_all(obj.serialize() for obj in self)
        }

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda switch: func in switch.alias(), self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(filter(lambda switch: any(f in switch.alias() for f in func), self))
        if isinstance(func, Switch):
            return self.copy([func])
        return self.copy(filter(func, self))

    def __bool__(self):
        return bool(self.switches)

    def __len__(self):
        return len(self.switches)

    def __iter__(self):
        return iter(self.switches)

    def __repr__(self):
        return repr(self.switches)