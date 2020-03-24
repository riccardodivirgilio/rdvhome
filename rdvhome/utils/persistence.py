# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals
from rdvhome.conf import settings
from rpy.functions.importutils import module_path
import os
def data_path(*args):
    if settings.DEBUG:
        return module_path("rdvhome", "data", *args)
    else:
        return os.path.join(os.path.expanduser('~/.rdvhome'), *args)