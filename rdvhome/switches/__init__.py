# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.conf import settings
from rdvhome.switches.base import SwitchList
from rdvhome.utils.importutils import import_string

def construct(n, class_path, active = True, **switch):
    return import_string(class_path)(**dict({'ordering': n+1}, **switch))

switches = SwitchList(
    #lazy construction so that we don't have any problem with recursion
    lambda: (
        construct(n, **switch)
        for n, switch in enumerate(settings.SWITCHES)
        if switch and switch.get('active', True)
    )
)