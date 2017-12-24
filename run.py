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
                philips('b1', 'Camera letto', ordering = 10, philips_id = 2, alias = []),
                philips('l1', 'Salone 1',     ordering =  1, philips_id = 1, alias = ['default']),
                philips('l2', 'Salone 2',     ordering =  2, philips_id = 3, alias = ['default']),
            )
        }
    )

if __name__ == '__main__':
    run_rdv_command_line()