# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys

def execute_from_command_line(argv = None, **opts):

    if sys.version_info[0] == 2:
        raise NotImplementedError('There is no support for python2. Please run python3.')

    from rdvhome.utils.require import require_module

    require_module(
        ['aiohttp', '2.3.6'],
        ['asyncio', None],
        ['six',     None],
        ['aiohttp-autoreload', None],
        ['django',  None],
        ['aioreactive', None],
        ['colour', None],
        ['django', None],
    )

    from rdvhome.conf import settings

    settings.update(opts)

    from rdvhome.cli.dispatch import DispatchCommand

    return DispatchCommand(argv).main()