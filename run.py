# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line

import uuid
import random

def timeout(min, max):
    return lambda switch, i: random.random() * (max-min) + min

def run_rdv_command_line():

    philips = lambda id, name, **opts: dict(
        id        = id,
        name      = name,
        username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
        ipaddress = "192.168.1.179",
        **opts
    )

    return execute_from_command_line(
        DEBUG    = uuid.getnode() == 180725258261487, #my laptop everything else is production.
        SWITCHES = {
            'rdvhome.switches.philips.PhilipsSwitch': (
                philips('lm', 'Salone',       ordering =  1, icon = "🛋", philips_id = 1, alias = ['default']),
                philips('lb', 'Salone Big',   ordering =  2, icon = "🛋", philips_id = 3, alias = ['default']),
                philips('br', 'Camera letto', ordering = 10, icon = "🛏", philips_id = 2, alias = []),
            ),
            'rdvhome.switches.controls.ControlSwitch': (
                dict(id = 'usa',      name = "USA",    ordering = 30, icon = "🇺🇸", colors = ['red', 'white', 'blue'], timeout = 3, automatic_on = 'default'),
                dict(id = 'artic',    name = "Artic",  ordering = 31, icon = "⛄",   colors = ['#bcf5ff', '#b2ffc5', '#87ffc7']),
                dict(id = 'random',   name = "Random", ordering = 32, icon = "🌐"),
                dict(id = 'loop',     name = "Random Loop", ordering = 33, icon = "🌐", timeout = timeout(5, 10)),
                dict(id = 'disco',    name = "Disco",  ordering = 34, icon = "🌐", timeout = timeout(0.3, 1.2)),
            )
        }
    )

if __name__ == '__main__':
    run_rdv_command_line()