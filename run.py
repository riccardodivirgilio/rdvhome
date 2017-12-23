# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys

if __name__ == '__main__':

    if sys.version_info[0] == 2:
        raise NotImplementedError('There is no support for python2. Please run python3.')

    from rdvhome.utils.require import require_module

    require_module(
        ['aiohttp', '2.3.6'],
        ['asyncio', None],
        ['six',     None],
        ['aiohttp-autoreload', None],
        ['django',  None]
    )

    from rdvhome.cli.main import execute_from_command_line

    router = dict(
        username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
        ipaddress = "192.168.1.179",
    )

    execute_from_command_line(
        DEBUG = True,
        SWITCHES = {
            'rdvhome.switches.philips.PhilipsSwitch': [
                dict(id = 'l1', name = 'Salone 1',     philips_id = 1, **router),
                dict(id = 'b1', name = 'Camera letto', philips_id = 2, **router),
                dict(id = 'l2', name = 'Salone 2',     philips_id = 3, **router),
            ]
        }
    )