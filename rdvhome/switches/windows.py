# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio

from rdvhome.conf import settings
from rdvhome.switches.base import HomekitSwitch, Switch, capabilities
from rdvhome.utils.gpio import get_gpio


class HomekitWindow(HomekitSwitch):

    def switch_name(self):
        return '%s %s' % (self.switch.name, self.event_name.title())

    def set_on(self, value):
        return super().set_on(value and self.event_name or 'stop')

class Window(Switch):

    homekit_class = None

    default_capabilities = capabilities(direction=True)

    timings = {
        'up': settings.DEBUG and 4 or 13,
        'down': settings.DEBUG and 4 or 12
    }

    homekit_class = HomekitWindow

    def __init__(self, id, gpio_power, gpio_direction, **opts):

        self.gpio_power = gpio_power
        self.gpio_direction = gpio_direction

        self._gpio = None

        super().__init__(id, **opts)

    def create_homekit_accessory(self, driver):
        yield self.homekit_class(driver=driver, switch=self, event_name = 'up')
        yield self.homekit_class(driver=driver, switch=self, event_name = 'down')

    async def start(self):
        #on start we make sure gpio is all off
        await self.stop()

    async def watch(self, interval=1):

        counters = {'up': 0, 'down': 0}

        while True:

            await asyncio.sleep(interval)

            for direction, moving in (await self.direction()).items():

                if moving:
                    counters[direction] += interval
                else:
                    counters[direction] = 0

                if counters[direction] >= self.timings[direction]:
                    await self.stop()
                    counters[direction] = 0

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        await self._gpio.setup_output(self.gpio_power)
        await self._gpio.setup_output(self.gpio_direction)

        return self._gpio

    async def direction(self):

        gpio = await self.setup_gpio()

        power_off = await gpio.input(self.gpio_power)
        going_up = await gpio.input(self.gpio_direction)

        return {
            'up': bool(not power_off and going_up),
            'down': bool(not power_off and not going_up),
        }

    async def status(self):
        return await self.send(** await self.direction())

    async def stop(self):

        gpio = await self.setup_gpio()

        await gpio.output(self.gpio_power, high=True)
        await gpio.output(self.gpio_direction, high=True)

        return await self.status()

    async def switch(self, direction=None, **opts):

        gpio = await self.setup_gpio()

        if not direction or direction == 'stop':
            return await self.stop()

        status = await self.direction()

        if not status[direction]:

            gpio = await self.setup_gpio()

            await gpio.output(self.gpio_direction, high=direction == "up")
            await gpio.output(self.gpio_power, high=False)

        return await self.status()
