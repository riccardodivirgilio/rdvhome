# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import capabilities, Switch, HomekitSwitch
from rdvhome.utils import json
from rdvhome.utils.colors import color_to_philips, philips_to_color, to_color
from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import to_data
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.keystore import KeyStore
from pyhap.const import CATEGORY_LIGHTBULB
from rdvhome.utils.colors import to_color, homekit_to_color, color_to_homekit
from rdvhome.conf import loop
from rdvhome.utils.decorators import debounce

import aiohttp
import asyncio

class HomekitLight(HomekitSwitch):

    category = CATEGORY_LIGHTBULB

    def setup_services(self):
        service = self.add_preload_service(
            'Lightbulb', 
            chars = list(self.discover_characteristics())
        )
        self.switch_service = service.configure_char(
            'On', 
            setter_callback = self.set_on,
            value = None
        )

        for attr in ('Hue', 'Saturation', 'Brightness'):
            if self.switch.default_capabilities.get('allow_%s' % attr.lower(), False):
                setattr(
                    self,
                    '%s_service' % attr.lower(),
                    service.configure_char(
                        attr, 
                        setter_callback = getattr(self, 'set_%s' % attr.lower()),
                        value = None
                    )
                )

    def discover_characteristics(self):
        if self.switch.default_capabilities.allow_hue:
            yield 'Hue'
        if self.switch.default_capabilities.allow_saturation:
            yield 'Saturation'
        if self.switch.default_capabilities.allow_brightness:
            yield 'Brightness'

    def set_saturation(self, value):
        print('Homekit -> Saturation', value, homekit_to_color(saturation = value))
        self.perform_switch(color = homekit_to_color(saturation = value))

    def set_hue(self, value):
        print('Homekit -> Hue', value, homekit_to_color(hue = value))
        self.perform_switch(color = homekit_to_color(hue = value))

    def set_brightness(self, value):
        print('Homekit -> Brightness', value, homekit_to_color(brightness = value))
        self.perform_switch(color = homekit_to_color(brightness = value))

    async def on_event(self, event):
        await super().on_event(event)

        for attr, value in color_to_homekit(event).items():
            print(attr, value)
            getattr(self, '%s_service' % attr).set_value(value)

class Light(Switch):

    homekit_class = HomekitLight

    store = KeyStore(prefix = 'philips')

    @property
    def default_capabilities(self):
        return capabilities(
            on         = True,
            hue        = bool(self.philips_id),
            saturation = bool(self.philips_id),
            brightness = bool(self.philips_id),
        )

    @property
    @to_data
    def philips_settings(self):

        if not self.gpio_relay:
            yield "on", False

        if self.philips_id:
            yield "brightness", 1
            yield "hue",        0.5
            yield "saturation", 1

    def __init__(self, id, philips_id = None, ipaddress = None, username = None, gpio_relay = None, gpio_status = None, **opts):

        self.philips_id  = philips_id
        self.ipaddress   = ipaddress
        self.username    = username

        self._gpio = None

        self.gpio_relay  = gpio_relay
        self.gpio_status = gpio_status

        super(Light, self).__init__(id, **opts)

    async def api_request(self, path = '', payload = None):

        assert self.ipaddress and self.username and self.philips_id

        path = 'http://%s/api/%s/lights/%s%s' % (
            self.ipaddress,
            self.username,
            self.philips_id,
            path
        )

        async with aiohttp.ClientSession() as session:
            async with session.put(path, json = payload) as response:
                return await response.json(loads = json.loads)

    async def watch(self):
        if self.gpio_status:

            status = await self.raspberry_status()

            while True:

                current = await self.raspberry_status()

                if not current == status:

                    status = current

                    await self.send(on = status)
               
                await asyncio.sleep(0.3)

    async def setup_gpio(self):

        if self._gpio:
            return self._gpio

        self._gpio = get_gpio()

        if self.gpio_relay:
            await self._gpio.setup_output(self.gpio_relay)

        if self.gpio_status:
            await self._gpio.setup_input(self.gpio_status)

        return self._gpio

    @debounce(1)
    async def raspberry_switch(self, on = True):

        gpio = await self.setup_gpio()

        await gpio.output(self.gpio_relay, high = False)
        await asyncio.sleep(0.025)
        await gpio.output(self.gpio_relay, high = True)

        if gpio.is_debug:
            await gpio.store.set(self.gpio_status, not on and 1 or 0)

    async def raspberry_status(self):

        gpio = await self.setup_gpio()

        return not await gpio.input(self.gpio_status)

    async def status(self, allow_philips = True):

        if self.gpio_relay:
            defaults = data(on = await self.raspberry_status())
        else:
            defaults = data()

        if self.philips_id and allow_philips:

            if self.username:
                response = await self.api_request()
                response = data(
                    on = response.state.on,
                    color = philips_to_color(
                        hue        = float(response.state.hue),
                        saturation = float(response.state.sat),
                        brightness = float(response.state.bri),
                    ),
                )

            else:
                #debug mode
                response = await self.store.get(self.id, self.philips_settings)

            response.update(defaults)
            return await self.send(**response)

        return await self.send(**defaults)

    @to_data
    def parse_command(self, on = None, color = None):

        if on is not None:
            yield 'on', bool(on)

        if color is not None:
            if self.username:
                yield from color_to_philips(color).items()
            else:
                yield from to_color(color).serialize().items()

    async def switch(self, on = None, color = None):
        payload = self.parse_command(on, color)

        if 'on' in payload and self.gpio_relay:
            on = payload.pop('on')
            if not on == await self.raspberry_status():
                await self.raspberry_switch(on)

        if payload:

            if self.philips_id:
                if self.username:
                    await self.api_request('/state', payload)
                else:
                    #debug mode
                    payload = data(
                        await self.store.get(self.id, self.philips_settings),
                        **payload
                    )
                    await self.store.set(self.id, payload)

        return await self.send(on = on, color = color, full = False)