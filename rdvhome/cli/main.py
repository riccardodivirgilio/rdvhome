# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys


def execute_from_command_line(argv = None, **opts):

    if sys.version_info[0] == 2:
        raise NotImplementedError('There is no support for python2. Please run python3.')

    from rpy.functions.require import require_module
    from rdvhome.conf import settings

    settings.update(opts)

    if settings.INSTALL_DEPENDENCIES:
        require_module(*settings.DEPENDENCIES.items())

    from rdvhome.cli.dispatch import DispatchCommand

    return DispatchCommand(argv).main()
