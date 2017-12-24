# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aioreactive.operators.concat import concat
from aioreactive.operators.merge import merge

from collections import OrderedDict

from functools import reduce

from operator import attrgetter, methodcaller

from rdvhome.switches.events import EventStream, subscribe
from rdvhome.utils.async import wait_all
from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import decorate, to_data
from rdvhome.utils.functional import first, iterate

import asyncio
import six

class Switch(EventStream):

    kind = 'switch'

    def __init__(self, id, name = None, alias = (), ordering = None, icon = None):
        self.id = id
        self.name = name
        self.alias = frozenset(iterate(self.id, alias, 'all'))
        self.ordering = ordering
        self.icon = icon

        super(Switch, self).__init__()

    @to_data
    def _send(self, on = None, **opts):
        yield 'id',         self.id
        yield 'name',       self.name
        yield 'kind',       self.kind
        yield 'icon',       self.icon
        yield 'alias',      self.alias
        yield 'ordering',   self.ordering

        if on is not None:
            yield 'on',     bool(on)
            yield 'off',    not bool(on)
            yield 'action', '/switch/%s/%s' % (self.id, on and 'off' or 'on')

        for key, value in opts.items():
            yield key, value

    def send(self, **opts):
        return super(Switch, self).send(self._send(**opts))

    async def switch(self, on = None):
        raise NotImplementedError

    async def status(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class SwitchList(object):

    def __init__(self, switches):
        self.switches = switches

    async def subscribe(self, func):
        return await wait_all(
            switch.subscribe(func)
            for switch in self
        )

    def get_switches(self):

        if callable(self._switches):
            self._switches = self._switches()

        if not isinstance(self._switches, (tuple, list, set, frozenset)):
            self._switches = tuple(iterate(self._switches))

        return self._switches

    def set_switches(self, values):
        self._switches = values

    switches = property(get_switches, set_switches)

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