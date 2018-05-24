# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.conf import settings
from rdvhome.switches.base import SwitchList
from rdvhome.utils.importutils import import_string

def construct(class_path, **switch):
    return import_string(class_path)(**switch)

switches = SwitchList(
    #lazy construction so that we don't have any problem with recursion
    lambda: (
        construct(**switch)
        for switch in settings.SWITCHES
    )
)