# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import six
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH
from rpy.functions.asyncio import run_all, wait_all
from rpy.functions.datastructures import data
from rpy.functions.decorators import to_data
from rpy.functions.functional import iterate

from rdvhome.switches.events import EventStream
from rdvhome.utils.colors import to_color


def capabilities(
    on=False,
    hue=False,
    saturation=False,
    brightness=False,
    direction=False,
    visible=True,
):
    return data(
        allow_on=on,
        allow_hue=hue,
        allow_saturation=saturation,
        allow_brightness=brightness,
        allow_direction=direction,
        visible=visible,
        on=False,
        hue=1,
        saturation=0,
        brightness=1,
        direction=None
    )


class HomekitSwitch(Accessory):

    category = CATEGORY_SWITCH

    def __init__(self, driver, switch, event_name = 'on'):

        self.switch = switch
        self.event_name = event_name

        super().__init__(
            driver=driver,
            display_name=self.switch_name(),
            #aid=random_aid(self.switch_id())
        )
        run_all(self.switch.subscribe(self.on_event), loop=self.driver.loop)
        self.setup_services()

    def switch_name(self):
        return self.switch.name

    def perform_switch(self, *args, **opts):
        run_all(self.switch.switch(*args, **opts), loop=self.driver.loop)

    def set_on(self, value):
        self.perform_switch(value)

    def setup_services(self):
        service = self.add_preload_service("Switch")
        self.switch_service = service.configure_char(
            "On", setter_callback=self.set_on, value=None
        )

    async def on_event(self, event):
        try:
            self.switch_service.set_value(event[self.event_name])
        except KeyError:
            pass


class Switch(EventStream):

    kind = "switch"
    default_aliases = ["all"]
    default_capabilities = capabilities(on=True)

    homekit_class = HomekitSwitch

    def __init__(self, id, name=None, alias=(), ordering=None, icon=None):
        self.id = id
        self.name = name or id
        self.alias = frozenset(iterate(self.id, alias, self.default_aliases, self.kind))
        self.ordering = ordering
        self.icon = icon
        self.state = data(self.default_capabilities)

        super().__init__()

    def create_homekit_accessory(self, driver):
        if self.homekit_class:
            return self.homekit_class(driver=driver, switch=self)

    @to_data
    def serialize(self):
        yield "id", self.id

        yield "name", self.name
        yield "kind", self.kind
        yield "icon", self.icon
        yield "alias", self.alias
        yield "ordering", self.ordering
        yield from self.state.items()

    async def assign_state(self, **opts):

        diff = {}

        for key, value in opts.items():
            try:
                if not self.state[key] == value:
                    diff[key] = self.state[key] = value
            except KeyError:
                diff[key] = self.state[key] = value

        if diff:
            return await super(Switch, self).send({'switches': {self.id: diff}})

    async def switch(self, *args, **opts):
        pass

    async def status(self, *args, **opts):
        pass

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.id)


class SwitchList(object):
    def __init__(self, switches):
        self.switches = switches

    async def subscribe(self, func):
        return await wait_all(switch.subscribe(func) for switch in self)

    async def watch(self):
        return await wait_all(switch.watch() for switch in self)

    async def start(self):
        return await wait_all(switch.start() for switch in self)

    def get_switches(self):

        if callable(self._switches):
            self._switches = self._switches()

        if not isinstance(self._switches, dict):
            self._switches = {s.id: s for s in iterate(self._switches)}

        return self._switches

    def set_switches(self, values):
        self._switches = values

    switches = property(get_switches, set_switches)

    async def status(self, *args, **opts):

        await wait_all(obj.status(*args, **opts) for obj in self)

        return {
            obj.id: obj.serialize()
            for obj in self
        }
        

    async def switch(self, *args, **opts):

        await wait_all(obj.switch(*args, **opts) for obj in self)

        return {
            obj.id: obj.serialize()
            for obj in self
        }

    def get(self, pk):
        return self.switches.get(pk)

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func=None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda switch: func in switch.alias, self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(
                filter(lambda switch: any(f in switch.alias for f in func), self)
            )
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
        return iter(self.switches.values())

    def __repr__(self):
        return repr(tuple(self.switches))
