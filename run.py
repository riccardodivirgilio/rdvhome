# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line

import uuid

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
                philips('br', 'Camera letto', ordering = 10, icon = "🛏", philips_id = 2, alias = []),
                philips('lm', 'Salone',       ordering =  1, icon = "🛋", philips_id = 1, alias = ['default']),
                philips('lb', 'Salone Big',   ordering =  2, icon = "🛋", philips_id = 3, alias = ['default']),
            ),
            'rdvhome.switches.scene.SceneSwitch': (
                dict(id = 'usa', name = "USA", ordering = 20, icon = "🇺🇸", directives = {
                    'lm': {'color': 'red',  'on': True},
                    'lb': {'color': 'blue', 'on': True},
                    'br': {'color': 'white'},
                }),
                dict(id = 'artic', name = "Artic", ordering = 21, icon = "⛄", directives = {
                    'lm': {'color': 'lime'},
                    'lb': {'color': 'lime'},
                    'br': {'color': 'lime'},
                }),
            )
        }
    )

if __name__ == '__main__':
    run_rdv_command_line()