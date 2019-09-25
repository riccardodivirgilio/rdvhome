# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line
from rdvhome.utils.gpio import has_gpio
from rpy.functions.decorators import to_data

import random
import uuid
import subprocess

RELAY1 = [27, 22, 10, 9, 11, 5, 6, 13]

RELAY2 = [14, 15, 18, 23, 24, 16, 20, 21]

INPUT = [2, 3, 4, 17, 25, 8, 7, 12]


def timeout(min, max):
    return lambda switch, i: random.random() * (max - min) + min


def run_rdv_command_line():

    control = lambda **opts: dict(
        class_path="rdvhome.switches.controls.ControlSwitch", **opts
    )

    @to_data
    def philips_control(**opts):
        yield "class_path", "rdvhome.switches.philips.PhilipsPoolControl"

        if has_gpio():
            yield "username", "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W"
            yield "ipaddress", "192.168.1.179"

        yield from opts.items()

    @to_data
    def tv(**opts):
        yield "class_path", "rdvhome.switches.tv.SamsungSmartTV"
        yield from opts.items()

    @to_data
    def light(philips_id=None, gpio_relay=None, gpio_status=None, **opts):

        if gpio_relay:
            assert gpio_relay in RELAY1 or gpio_relay in RELAY2, "%s not in %s" % (
                gpio_relay,
                ", ".join(map(str, (*RELAY1, *RELAY2))),
            )
            yield "gpio_relay", gpio_relay

        if gpio_status:
            assert gpio_status in INPUT
            yield "gpio_status", gpio_status

        if philips_id:
            yield "philips_id", philips_id
            yield from philips_control().items()

        yield "class_path", "rdvhome.switches.philips.Light"

        yield from opts.items()

    @to_data
    def window(gpio_up, gpio_down, **opts):
        if False:
            for pin in (gpio_up, gpio_down):
                assert pin in RELAY1 or pin in RELAY2, "%s not in %s" % (
                    pin,
                    ", ".join(map(str, (*RELAY1, *RELAY2))),
                )

            yield "class_path", "rdvhome.switches.windows.Window"
            yield "gpio_up", gpio_up
            yield "gpio_down", gpio_down

            yield from opts.items()

    return execute_from_command_line(
        RASPBERRY_RELAY1=RELAY1,
        RASPBERRY_RELAY2=RELAY2,
        RASPBERRY_INPUT=INPUT,
        INSTALL_DEPENDENCIES=True,
        DEBUG=not has_gpio(),  # raspberry is production.
        SWITCHES=[
            philips_control(id="philips_pool", name="Philips Pool", icon="💡"),
            light(
                id="spotlight_kitchen",
                name="Kitchen Light",
                icon="🍽",
                alias=[],
                gpio_relay=24,
                gpio_status=17,
            ),
            light(
                id="led_kitchen",
                name="Kitchen Led",
                icon="🍽",
                philips_id=6,
                alias=["default"],
            ),
            light(
                id="spotlight_living_room",
                name="Living Room Light",
                icon="🛋",
                alias=[],
                gpio_relay=23,
                gpio_status=2,
            ),
            light(
                id="led_living_room",
                name="Living Room Led",
                icon="🛋",
                philips_id=1,
                gpio_relay=20,
                gpio_status=4,
                alias=["default"],
            ),
            tv(id="tv", name="TV", icon="📺", alias=[], ipaddress="192.168.1.227"),
            light(
                id="spotlight_tv",
                name="TV Light",
                icon="📺",
                alias=[],
                gpio_relay=15,
                gpio_status=25,
            ),
            light(
                id="led_tv",
                name="TV Led",
                icon="📺",
                philips_id=3,
                gpio_relay=20,
                gpio_status=4,
                alias=["default"],
            ),
            light(
                id="spotlight_entrance",
                name="Entrance Light",
                icon="🚪",
                alias=[],
                gpio_relay=18,
                gpio_status=7,
            ),
            light(
                id="led_bathroom_entrance",
                name="Entrance Bathroom",
                icon="🚽",
                alias=[],
                philips_id=5,
            ),
            light(
                id="spotlight_bedroom",
                name="Bedroom Light",
                icon="🛏",
                alias=[],
                gpio_relay=21,
                gpio_status=3,
            ),
            light(
                id="led_bedroom",
                name="Bedroom Led",
                icon="🛏",
                philips_id=2,
                gpio_relay=14,
                gpio_status=8,
                alias=[],
            ),
            light(
                id="led_bathroom_bedroom",
                name="Bedroom Bathroom",
                icon="🚽",
                philips_id=4,
                alias=[],
            ),
            light(
                id="spotlight_room",
                name="Studio Light",
                icon="📚",
                alias=[],
                gpio_relay=16,
                gpio_status=12,
            ),
            light(
                id="lamp_room",
                name="Studio Lamp",
                icon="💡",
                philips_id=7,
                alias=["default"],
            ),
            window(
                id="window_kitchen",
                name="Kitchen Window",
                gpio_up=6,
                gpio_down=13,
                icon="☀️",
            ),
            window(
                id="window_living_room",
                name="Living Room Window",
                gpio_up=11,
                gpio_down=5,
                icon="☀️",
            ),
            window(
                id="window_tv", name="TV Window", gpio_up=22, gpio_down=27, icon="☀️"
            ),
            control(
                id="usa",
                name="USA",
                icon="🇺🇸",
                colors=[
                    dict(hue=1, saturation=1, brightness=1),
                    dict(hue=1, saturation=0, brightness=1),
                    dict(hue=0.66, saturation=1, brightness=1),
                ],
                timeout=3,
                automatic_on="default",
            ),
            control(
                id="natural",
                name="Naturale",
                icon="🌞",
                colors=[{"hue": 0.13, "saturation": 0.6, "brightness": 1.0}],
                automatic_on="default",
            ),
            control(
                id="artic",
                name="Artic",
                icon="⛄",
                colors=["#bcf5ff", "#b2ffc5", "#87ffc7"],
            ),
            control(id="random", name="Random", icon="❓"),
            control(id="loop", name="Random Loop", icon="♾️", timeout=timeout(30, 60)),
            control(
                id="hloop",
                name="Random Hipster Loop",
                icon="🤓",
                timeout=timeout(30, 60),
                colors=lambda switch, i: dict(
                    saturation=random.random() * 0.25 + 0.15, hue=random.random()
                ),
            ),
            control(
                id="disco",
                name="Disco",
                icon="🌐",
                timeout=timeout(0.3, 1.2),
                automatic_on="default",
            ),
        ],
    )


if __name__ == "__main__":
    run_rdv_command_line()
