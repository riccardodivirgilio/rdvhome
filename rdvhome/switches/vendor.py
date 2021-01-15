# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import six
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH
from rpy.functions.asyncio import run_all, wait_all
from rpy.functions.datastructures import data
from rpy.functions.decorators import to_data
from rpy.functions.functional import iterate

from rdvhome.switches.events import EventStream
from rdvhome.utils.colors import to_color

from rdvhome.switches.base import Switch

class VendorSwitch(Switch):
    pass
