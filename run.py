# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

if __name__ == '__main__':

    from rdvhome.cli.main import execute_from_command_line

    router = dict(
        username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
        ipaddress = "192.168.1.179",
    )

    execute_from_command_line(
        DEBUG = True,
        SWITCHES = {
            'rdvhome.switches.philips.PhilipsSwitch': [
                dict(id = 'b1', name = 'Camera letto', philips_id = 2, alias = [], **router),
                dict(id = 'l1', name = 'Salone 1',     philips_id = 1, alias = ['default'], **router),
                dict(id = 'l2', name = 'Salone 2',     philips_id = 3, alias = ['default'], **router),
            ]
        }
    )