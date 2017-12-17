# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.utils.module_loading import import_string

from rdvhome.toggles.base import ToggleCollection

all_toggles = ToggleCollection(
    import_string(collection)
    for collection in settings.TOGGLES
)