# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH

from rdvhome.switches.events import EventStream
from rdvhome.utils.async import run_all, wait_all
from rdvhome.utils.colors import to_color
from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import to_data
from rdvhome.utils.functional import iterate

import six

def capabilities(on = False, hue = False, saturation = False, brightness = False, direction = False, visibility = True):
    return data(
        allow_on         = on,
        allow_hue        = hue,
        allow_saturation = saturation,
        allow_brightness = brightness,
        allow_direction  = direction,
        allow_visibility = visibility
    )

class HomekitSwitch(Accessory):

    category = CATEGORY_SWITCH

    def __init__(self, driver, switch):
        super().__init__(
            driver = driver,
            display_name = switch.name,
            #aid = abs(hash(switch.id))
        )
        self.switch = switch

        run_all(
            self.switch.subscribe(self.on_event),
            loop = self.driver.loop
        )

        self.setup_services()

    def perform_switch(self, *args, **opts):
        run_all(self.switch.switch(*args, **opts), loop = self.driver.loop)

    def set_on(self, value):
        self.perform_switch(value)

    def setup_services(self):
        service = self.add_preload_service('Switch')
        self.switch_service = service.configure_char(
            'On',
            setter_callback = self.set_on,
            value = None
        )

    async def on_event(self, event):
        try:
            self.switch_service.set_value(event.on)
        except AttributeError:
            pass

class Switch(EventStream):

    kind = 'switch'
    default_aliases = ['all']
    default_capabilities = capabilities(on = True)

    homekit_class = HomekitSwitch

    def __init__(self, id, name = None, alias = (), ordering = None, icon = None):
        self.id = id
        self.name = name or id
        self.alias = frozenset(iterate(self.id, alias, self.default_aliases, self.kind))
        self.ordering = ordering
        self.icon = icon
        self.capabilities = self.default_capabilities.copy()

        super().__init__()

    def create_homekit_accessory(self, driver):
        if self.homekit_class:
            return self.homekit_class(driver = driver, switch = self)

    async def watch_switch(self):
        pass

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

    async def send(self, **opts):
        return await super(Switch, self).send(self._send(**opts))

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

    async def watch(self):
        return await wait_all(
            switch.watch()
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