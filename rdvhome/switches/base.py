# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.events import EventStream
from rdvhome.utils.async import wait_all
from rdvhome.utils.colors import to_color
from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import to_data
from rdvhome.utils.functional import iterate

import six

def capabilities(on = False, hue = False, saturation = False, brightness = False):
    return data(
        allow_on         = on,
        allow_hue        = hue,
        allow_saturation = saturation,
        allow_brightness = brightness,
    )

class Switch(EventStream):

    kind = 'switch'
    default_aliases = ['all']
    default_capabilities = capabilities(
        on         = True,
        hue        = True,
        saturation = True,
        brightness = True,
    )

    def __init__(self, id, name = None, alias = (), ordering = None, icon = None):
        self.id = id
        self.name = name or id
        self.alias = frozenset(iterate(self.id, alias, self.default_aliases, self.kind))
        self.ordering = ordering
        self.icon = icon
        self.capabilities = self.default_capabilities.copy()

        super(Switch, self).__init__()

    @to_data
    def _send(self, on = None, color = None, intensity = None, full = True, **opts):
        yield 'id',         self.id

        if full:
            yield 'name',       self.name
            yield 'kind',       self.kind
            yield 'icon',       self.icon
            yield 'alias',      self.alias
            yield 'ordering',   self.ordering

            yield from self.capabilities.items()

        if on is not None:
            yield 'on',  bool(on)
            yield 'off', not bool(on)

        if color is not None:
            yield from to_color(color).serialize().items()

        if intensity is not None:
            yield 'intensity', intensity

        yield from opts.items()

    def send(self, **opts):
        return super(Switch, self).send(self._send(**opts))

    async def switch(self, *args, **opts):
        raise NotImplementedError

    async def status(self, *args, **opts):
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