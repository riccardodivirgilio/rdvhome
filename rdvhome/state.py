# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.conf import settings
from rdvhome.switches.base import SwitchList
from rdvhome.controllers.base import ControllerList
from rpy.functions.importutils import import_string

def construct(n, class_path, **switch):
    print(class_path, switch['id'])
    return import_string(class_path)(**dict({"ordering": n + 1}, **switch))

switches, controls = (
    cls(
        # lazy construction so that we don't have any problem with recursion
        lambda opts = opts: (
            construct(n, **switch)
            for n, switch in enumerate(opts)
            if switch and switch.get("active", True)
        )
    )
    for cls, opts in ((SwitchList, settings.SWITCHES), (ControllerList, settings.CONTROLS))
)