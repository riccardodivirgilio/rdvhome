# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os

from rpy.functions.importutils import module_path

from rdvhome.conf import settings


def data_path(*args):
    if settings.DEBUG:
        return module_path("rdvhome", "data", *args)
    else:
        return os.path.join(os.path.expanduser('~/.rdvhome'), *args)
