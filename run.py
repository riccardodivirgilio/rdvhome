# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

if __name__ == '__main__':

    from rdvhome.cli.main import execute_from_command_line

    philips = lambda id, name, **opts: dict(
        id        = id,
        name      = name,
        username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
        ipaddress = "192.168.1.179",
        **opts
    )

    execute_from_command_line(
        DEBUG = True,
        SWITCHES = {
            'rdvhome.switches.philips.PhilipsSwitch': (
                philips('b1', 'Camera letto', philips_id = 2, alias = []),
                philips('l1', 'Salone 1',     philips_id = 1, alias = ['default']),
                philips('l2', 'Salone 2',     philips_id = 3, alias = ['default']),
            )
        }
    )