from rdvhome.controllers.base import AbstractController as BaseController
from rdvhome.state import switches
import asyncio
import aiohttp
from rdvhome.switches.base import Switch
from rpy.functions.datastructures import data
from rdvhome.signals import dispatch_switch
from rpy.functions.functional import first, last
import time

def make_default_settings( 

        automatic_on=None,
        automatic_off=None,
        filter=Switch.kind,
        colors=None,
        timeout=None,
        effect=None,

        ):

        return data(
            filter = filter,
            colors = colors,
            timeout = timeout,
            automatic_on = automatic_on,
            automatic_off = automatic_off,
            effect = effect,
        )

class Controller(BaseController):

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.current = None
        self.power = {
            key: make_default_settings(**value)
            for key, value in self.power.items()
        }

    @property
    def settings(self):
        if self.current:
            return self.power[self.current.id]

    async def sync_switches(self):
        for s in switches.filter(tuple(self.power.keys())):
            await self.update_switch(s, allow_on = True, on = s == self.current)

    async def switch_power(self, switches, power):
        if not power:
            self.current = switch = None
        else:
            self.current = switch = first(switches)

            if self.settings.automatic_on:
                await dispatch_switch(
                    settings.automatic_on,
                    power = True
                )
            if self.settings.automatic_off:
                await dispatch_switch(
                    settings.automatic_off,
                    power = True
                )

        await self.sync_switches()
        
        if power and not timeout:
            await asyncio.sleep(1)
            if self.current == switch:
                self.current = None
                await self.sync_switches()

    def timout_next_interval(self, i, default = 0.25):
        if self.current:
            return self.settings.timout or 0.25
        return default

    async def timout_handler(self, i):
        print(time.time(), i)

    async def watch(self):
        await self.sync_switches()
        #await self.create_periodic_task(self.timout_handler, interval = self.timout_next_interval)

