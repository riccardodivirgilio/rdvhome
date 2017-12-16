# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.server import PHILIPS
from rdvhome.toggles.base import Toggle, ToggleList

class PhilipsToggle(Toggle):
    pass

class PhilipsToggleList(ToggleList):
    pass

toggles_list = PhilipsToggleList(
    PHILIPS, (
        PhilipsToggle('led1')
    )
)