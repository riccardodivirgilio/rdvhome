# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import time
import traceback

import aiohttp
from pyhap.const import CATEGORY_LIGHTBULB
from rpy.functions.datastructures import data

from rdvhome.switches import switches
from rdvhome.switches.base import HomekitSwitch, Switch, capabilities
from rdvhome.utils import json
from rdvhome.utils.colors import (
    HSB, color_to_homekit, color_to_philips, homekit_to_color,
    philips_to_color, to_color
)
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.keystore import KeyStore


def remove_none(**d):
    return d.__class__((key, value) for key, value in d.items() if value is not None)


def debounce(s):
    """Decorator ensures function that can only be called once every `s` seconds.
    """

    def decorate(f):
        async def wrapped(self, *args, **kwargs):
            self._t = None
            t_ = time.time()
            result = None
            if self._t is None or t_ - self._t >= s:
                result = await f(self, *args, **kwargs)
                self._t = time.time()
            return result

        return wrapped

    return decorate


class HomekitLight(HomekitSwitch):

    category = CATEGORY_LIGHTBULB

    def setup_services(self):
        service = self.add_preload_service(
            "Lightbulb", chars=list(self.discover_characteristics())
        )
        self.switch_service = service.configure_char(
            "On", setter_callback=self.set_on, value=None
        )

        for attr in ("Hue", "Saturation", "Brightness"):
            if self.switch.default_capabilities.get("allow_%s" % attr.lower(), False):
                setattr(
                    self,
                    "%s_service" % attr.lower(),
                    service.configure_char(
                        attr,
                        setter_callback=getattr(self, "set_%s" % attr.lower()),
                        value=None,
                    ),
                )

    def discover_characteristics(self):
        if self.switch.default_capabilities.allow_hue:
            yield "Hue"
        if self.switch.default_capabilities.allow_saturation:
            yield "Saturation"
        if self.switch.default_capabilities.allow_brightness:
            yield "Brightness"

    def set_saturation(self, value):
        print("Homekit -> Saturation", value, homekit_to_color(saturation=value))
        self.perform_switch(color=homekit_to_color(saturation=value))

    def set_hue(self, value):
        print("Homekit -> Hue", value, homekit_to_color(hue=value))
        self.perform_switch(color=homekit_to_color(hue=value))

    def set_brightness(self, value):
        print("Homekit -> Brightness", value, homekit_to_color(brightness=value))
        self.perform_switch(color=homekit_to_color(brightness=value))

    async def on_event(self, event):
        await super().on_event(event)

        for attr, value in color_to_homekit(event).items():
            try:
                getattr(self, "%s_service" % attr).set_value(value)
            except AttributeError:
                pass


class PhilipsBase(Switch):

    store = KeyStore(prefix="philips")

    def __init__(self, id, ipaddress=None, username=None, **opts):

        self.ipaddress = ipaddress
        self.username = username

        super().__init__(id, **opts)

    async def api_request(self, path="", payload=None):

        path = "http://%s/api/%s/lights/%s" % (self.ipaddress, self.username, path)

        async with aiohttp.ClientSession() as session:
            if payload:
                async with session.put(path, json=payload) as response:
                    return await response.json(loads=json.loads)
            else:
                async with session.get(path) as response:
                    return await response.json(loads=json.loads)


class Light(PhilipsBase):

    homekit_class = HomekitLight

    @property
    def default_capabilities(self):
        return capabilities(
            on=True,
            hue=bool(self.philips_id and self.supports_hue),
            saturation=bool(self.philips_id and self.supports_hue),
            brightness=bool(self.philips_id and self.supports_hue),
        )

    philips_default_settings = data(
        on=False, allow_on=True, hue=0.5, brightness=1, saturation=1
    )

    def __init__(self, id, philips_id=None, gpio_relay=None, gpio_status=None, supports_hue = True, **opts):

        self._gpio = None

        self.philips_id = philips_id
        self.gpio_relay = gpio_relay
        self.gpio_status = gpio_status
        self.supports_hue = supports_hue

        super().__init__(id, **opts)

    async def api_request(self, path="", *args, **opts):
        return await super().api_request(
            path="%s%s" % (self.philips_id, path), *args, **opts
        )

    async def watch(self, interval=0.3):

        if self.gpio_status:

            status = await self.is_on()

            while True:

                current = await self.is_on()

                if not current == status:

                    status = current

                    await self.send(on=status)

                await asyncio.sleep(interval)

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
    async def raspberry_switch(self, on=True):

        gpio = await self.setup_gpio()

        await gpio.output(self.gpio_relay, high=False)
        await asyncio.sleep(0.025)
        await gpio.output(self.gpio_relay, high=True)

        if gpio.is_debug:
            await gpio.store.set(self.gpio_status, not on and 1 or 0)

    async def is_on(self):

        if self.gpio_status:
            gpio = await self.setup_gpio()
            return not await gpio.input(self.gpio_status)

        status = await self.saved_status()
        return status.on

    async def saved_status(self):
        return await self.store.get(self.id, self.philips_default_settings)

    async def update_status(self, **payload):
        payload = data(await self.saved_status(), **payload)
        await self.store.set(self.id, payload)

    async def status(self):

        if self.gpio_status:
            defaults = data(on=await self.is_on())
        else:
            defaults = data()

        if self.philips_id:

            response = await self.saved_status()
            response.update(defaults)

            return await self.send(**response)

        return await self.send(**defaults)

    async def switch(self, on=None, color=None):

        print("stick", on, color)

        if on is not None and self.gpio_relay:
            if not on == await self.is_on():
                await self.raspberry_switch(on)

        if self.philips_id and self.username:

            request = data()

            if on is not None:
                request.on = bool(on)

            if color is not None:
                request.update(color_to_philips(color))

            if request:
                await self.api_request(path="/state", payload=request)

        await self.update_status(**remove_none(on=on, **to_color(color).serialize()))

        return await self.send(on=on, color=color, full=False)


class PhilipsPoolControl(PhilipsBase):

    default_capabilities = capabilities(visibility=False)

    philips_initial_color = HSB(
        hue=0.12845044632639047, saturation=0.5511811023622047, brightness=1
    )

    homekit_class = None

    async def status(self):
        return await self.send()

    async def watch(self, interval=3):

        if not self.username:
            return

        lights = {
            str(light.philips_id): light
            for light in switches.filter(
                lambda switch: getattr(switch, "philips_id", None)
            )
        }

        while True:

            try:
                await self.update_lights(lights)
            except Exception as e:
                print(e)
                traceback.print_tb(e.__traceback__)

            await asyncio.sleep(interval)

    async def update_lights(self, lights):

        payload = await self.api_request()

        for philips_id, response in payload.items():

            light = lights.get(philips_id)

            if light:

                is_changed = False

                current_on = response.state.reachable and response.state.on or False
                current_allow_on = response.state.reachable or bool(light.gpio_relay)
                current_color = philips_to_color(
                    hue=float(response.state.hue),
                    saturation=float(response.state.sat),
                    brightness=float(response.state.bri),
                )

                saved = await light.saved_status()

                saved_on = saved.on
                saved_allow_on = saved.allow_on
                saved_color = to_color(saved)

                if current_color == self.philips_initial_color:

                    if response.state.reachable:

                        if saved_color == self.philips_initial_color:
                            saved_color = to_color(light.philips_default_settings)
                        else:
                            saved_color.brightness = 1

                        await light.switch(color=saved_color)
                        current_color = saved_color
                        is_changed = True
                        print("INITIAL_COLOR", light, response.state)

                if not light.gpio_relay and (
                    not current_on == saved_on or not current_allow_on == saved_allow_on
                ):
                    is_changed = True

                    print("DIFFERENT ON", light)

                if not current_color == saved_color:
                    is_changed = True

                    print("DIFFERENT COLOR", light)

                if is_changed:

                    # if something changed, then we need to update the status and trigger notifications
                    await light.update_status(
                        on=current_on,
                        allow_on=current_allow_on,
                        **current_color.serialize()
                    )
                    await light.status()
