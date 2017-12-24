# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.conf import settings
from rdvhome.switches.base import SwitchList
from rdvhome.utils.importutils import import_string

switches = SwitchList(
    #lazy construction so that we don't have any problem with recursion
    lambda: (
        import_string(path)(**switch)
        for path, switches in settings.SWITCHES.items()
        for switch in switches
    )
)