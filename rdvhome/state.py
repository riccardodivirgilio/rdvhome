

from rdvhome.conf import settings

from rpy.functions.asyncio import wait_all
from rpy.functions.functional import iterate
from rpy.functions.importutils import import_string

import six

class SwitchList(object):
    def __init__(self, switches):
        self.switches = switches

    def get_switches(self):

        if callable(self._switches):
            self._switches = self._switches()

        if not isinstance(self._switches, dict):
            self._switches = {s.id: s for s in iterate(self._switches)}

        return self._switches

    def set_switches(self, values):
        self._switches = values

    switches = property(get_switches, set_switches)

    async def subscribe(self, func):
        return await wait_all(switch.subscribe(func) for switch in self)

    async def watch(self):
        return await wait_all(switch.watch() for switch in self)

    async def start(self):
        return await wait_all(switch.start() for switch in self)

    def get(self, pk):
        return self.switches.get(pk)

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func=None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda switch: func in switch.alias, self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(filter(lambda switch: any(f in switch.alias for f in func), self))
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

def construct(n, class_path, **switch):
    return import_string(class_path)(**dict({"ordering": n + 1}, **switch))

switches, controllers = (
    SwitchList(
        # lazy construction so that we don't have any problem with recursion
        lambda opts=opts: (
            construct(n, **switch)
            for n, switch in enumerate(opts)
            if switch and switch.get("active", True)
        )
    )
    for opts in (settings.SWITCHES, settings.CONTROLS)
)