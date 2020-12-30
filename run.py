# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line
from rdvhome.utils.gpio import has_gpio
from rpy.functions.decorators import to_data
from rdvhome.utils.colors import HSB, to_color, random_color
import random
import uuid
import subprocess
from functools import partial

RELAY1 = [6, 5, 9, 13, 11, 27, 22, 10]

RELAY2 = [14, 15, 18, 23, 24, 16, 20, 21]

INPUT = [2, 3, 4, 17, 25, 8, 7, 12]


# RELAY 2
# F1_POWER:     6
# F1_DIRECTION: 5
# F2_POWER:     9
# F2_DIRECTION: 13
# F3_POWER:     11
# F3_DIRECTION: 27

NANOLEAF_IP = "192.168.1.115"
NANOLEAF_ACCESS_TOKEN = "lWI4Ymlb9WkrELgfnXZBlQyeuXljzaw1"

PHILIPS_IP = "192.168.1.179"
PHILIPS_ACCESS_TOKEN = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W"

GPIOSERVER_IP = "192.168.1.87"
GPIOSERVER_ACCESS_TOKEN = "lol"

def random_factor(factor):
    return (random.random() * 2 -1) * factor

def perturbation(switch = None, i = None, color = None, factor = 0.04):

    if not color:
        return random_color()

    color = to_color(color)

    return dict(
        saturation=min(max((color.saturation + random_factor(factor)), 0.5), 1.0), hue=(color.hue + random_factor(factor)) % 1
    )

def timeout(min, max):
    return lambda switch, i: random.random() * (max - min) + min


def run_rdv_command_line():

    control = lambda **opts: dict(
        class_path="rdvhome.switches.controls.ControlSwitch", **opts
    )

    @to_data
    def philips(**opts):
        yield "class_path", "rdvhome.switches.api.PhilipsControl"

        yield "access_token", PHILIPS_ACCESS_TOKEN
        yield "ipaddress", PHILIPS_IP

        yield from opts.items()

    @to_data
    def nanoleaf(**opts):
        yield "class_path", "rdvhome.switches.api.NanoleafControl"

        yield "access_token", NANOLEAF_ACCESS_TOKEN
        yield "ipaddress", NANOLEAF_IP

        yield from opts.items()

    @to_data
    def gpioserver(**opts):
        yield "class_path", "rdvhome.switches.api.GPIOControl"

        yield "access_token", GPIOSERVER_ACCESS_TOKEN
        yield "ipaddress", GPIOSERVER_IP

        yield from opts.items()

    @to_data
    def tv(**opts):
        yield "class_path", "rdvhome.switches.tv.SamsungSmartTV"
        yield from opts.items()

    @to_data
    def device(philips_id=None, gpio_relay=None, gpio_status=None, **opts):

        if gpio_relay:
            assert gpio_relay in RELAY1 or gpio_relay in RELAY2, "%s not in %s" % (
                gpio_relay,
                ", ".join(map(str, (*RELAY1, *RELAY2))),
            )

        if gpio_status:
            assert gpio_status in INPUT

        if gpio_status or gpio_relay:
            yield "gpioserver", dict(gpio_relay = gpio_relay, gpio_status = gpio_status)

        if philips_id:
            yield "philips", dict(philips_id = philips_id)

        yield "class_path", "rdvhome.switches.devices.Device"

        yield from opts.items()

    @to_data
    def window(gpio_power, gpio_direction, **opts):
        for pin in (gpio_power, gpio_direction):
            assert pin in RELAY1 or pin in RELAY2, "%s not in %s" % (
                pin,
                ", ".join(map(str, (*RELAY1, *RELAY2))),
            )

        yield "class_path", "rdvhome.switches.devices.Device"
        yield "gpioserver", dict(gpio_power = gpio_power, gpio_direction = gpio_direction)

        yield from opts.items()

    return execute_from_command_line(
        RASPBERRY_RELAY1=RELAY1,
        RASPBERRY_RELAY2=RELAY2,
        RASPBERRY_INPUT=INPUT,
        INSTALL_DEPENDENCIES=True,
        DEBUG=not has_gpio(),  # raspberry is production.
        SWITCHES=[
            philips(id="philips"),
            nanoleaf(id="nanoleaf"),
            gpioserver(id="gpioserver"),


            device(
                id="led_kitchen",
                name="Kitchen Led",
                icon="🍽",
                philips_id=6,
                alias=["default"],
            ),
            device(
                id="spotlight_kitchen",
                name="Kitchen Light",
                icon="🍽",
                alias=[],
                gpio_relay=24,
                gpio_status=17,
            ),
            device(
                id="spotlight_living_room",
                name="Living Room Light",
                icon="🛋",
                alias=[],
                gpio_relay=23,
                gpio_status=2,
            ),
            device(
                id="led_living_room",
                name="Living Room Led",
                icon="🛋",
                philips_id=1,
                gpio_relay=20,
                gpio_status=4,
                alias=["default"],
            ),
            #tv(id="tv", name="TV", icon="📺", alias=[], ipaddress="192.168.1.235"),
            device(
                id="led_tv",
                name="TV Led",
                icon="📺",
                philips_id=3,
                gpio_relay=20,
                gpio_status=4,
                alias=["default"],
            ),
            device(
                id="spotlight_tv",
                name="TV Light",
                icon="📺",
                alias=[],
                gpio_relay=15,
                gpio_status=25,
            ),
            device(
                id="nanoleaf_tv",
                name="TV Light Panel",
                icon="📺",
                alias=["default", 'nanoleaf'],
            ),

            device(
                id="spotlight_entrance",
                name="Entrance Light",
                icon="🚪",
                alias=[],
                gpio_relay=18,
                gpio_status=7,
            ),
            device(
                id="led_bathroom_entrance",
                name="Bathroom Entrance",
                icon="🚽",
                alias=[],
                philips_id=5,
            ),
            device(
                id="led_bedroom",
                name="Bedroom Led",
                icon="🛏",
                philips_id=2,
                gpio_relay=14,
                gpio_status=8,
                alias=[],
            ),
            device(
                id="spotlight_bedroom",
                name="Bedroom Light",
                icon="🛏",
                alias=[],
                gpio_relay=21,
                gpio_status=3,
            ),
            device(
                id="led_bathroom_bedroom",
                name="Bathroom Bedroom",
                icon="🚽",
                philips_id=4,
                alias=[],
            ),
            device(
                id="spotlight_room",
                name="Studio Light",
                icon="📚",
                alias=[],
                gpio_relay=16,
                gpio_status=12,
            ),
            device(
                id="led_room",
                name="Studio Led",
                icon="💡",
                philips_id=8,
                alias=["default"],
            ),
            device(
                id="lamp_room",
                name="Studio Lamp",
                icon="💡",
                philips_id=7,
                alias=["default"],
            ),
            device(
                id="lamp_hipster_room",
                name="Studio Hipster Lamp",
                icon="💡",
                philips_id=9,
                alias=["default"],
            ),
            window(
                id="window_kitchen",
                name="Kitchen Window",
                gpio_power=5,
                gpio_direction=6,
                icon="☀️",
            ),
            window(
                id="window_living_room",
                name="Living Room Window",
                gpio_power=9,
                gpio_direction=13,
                icon="☀️",
            ),
            window(
                id="window_tv",
                name="TV Window",
                gpio_power=11,
                gpio_direction=27,
                icon="☀️",
            ),
            #control(id="random", name="Random", icon="❓", effect = 'Color Burst'),
            #control(
            #    id="hloop",
            #    name="Random Loop",
            #    icon="🤓",
            #    timeout=timeout(5, 10),
            #    colors=perturbation,
            #),
            #control(
            #    id="natural",
            #    name="Naturale",
            #    icon="🌞",
            #    colors=to_color({"hue": 0.13, "saturation": 0.6}),
            #    automatic_on="default",
            #    effect = 'Flames'
            #),
            #control(
            #    id="disco",
            #    name="Disco",
            #    icon="🌐",
            #    timeout=timeout(0.3, 1.2),
            #    automatic_on=["default", "nanoleaf"],
            #    effect = 'Fireworks'
            #),
            #*(
            #    control(
            #        id = 'nanoleaf_%s' % (effect.lower().replace(' ', '_')),
            #        name = effect,
            #        icon = i,
            #        automatic_on = ['nanoleaf'],
            #        effect = effect,
            #        colors = color
            #    )
            #    for i, effect, color in (
            #        ('🌲', 'Forest', partial(perturbation, color = {'hue': 0.297, 'saturation': 0.6}, factor = 0.15)),
            #        ('🎉', 'Inner Peace', None),
            #        ('🎉', 'Meteor Shower', None),
            #        ('🐟', 'Nemo', partial(perturbation, color = {'hue': 0.080, 'saturation': 0.90})),
            #        ('🎉', 'Northern Lights', None),
            #        ('🎉', 'Paint Splatter', None),
            #        ('🎉', 'Pulse Pop Beats', None),
            #        ('🎉', 'Rhythmic Northern Lights', None),
            #        ('🎉', 'Ripple', None),
            #        ('❤️', 'Romantic', partial(perturbation, color = {'hue': 0.8446, 'saturation': 1}, factor = 0.15)),
            #        ('⛄', 'Snowfall', partial(perturbation, color = {'hue': 0.5952, 'saturation': 0.50})),
            #        ('🎉', 'Sound Bar', None),
            #        ('🎉', 'Streaking Notes', None),
            #    )
            #),
        ],
    )


if __name__ == "__main__":
    run_rdv_command_line()
