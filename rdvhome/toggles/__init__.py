# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import defaultdict

from rdvhome.server import RASPBERRY

local_toggles = local_toggles.filter(lambda toggle: toggle.is_local())

toggle_registry = defaultdict(ToggleList)
for toggle in local_toggles:
    toggle_registry[toggle.id].register(toggle)
    toggle_registry['all'].register(toggle)
    for name in toggle.alias:
        toggle_registry[name].register(toggle)