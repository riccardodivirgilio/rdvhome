# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys

if __name__ == '__main__':

    if sys.version_info[0] == 2:
        raise NotImplementedError('There is no support for python2. Please run python3.')

    from rdvhome.utils.require import require_module

    require_module(
        ['aiohttp', None],
        ['asyncio', None],
        ['six',     None],
        ['aiohttp-autoreload', None]
    )

    from rdvhome.cli.main import execute_from_command_line

    execute_from_command_line()