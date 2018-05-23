# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils import json
from rdvhome.utils.importutils import module_path

import os

class KeyStore(object):

    encoder   = json
    extension = '.json'

    def __init__(self, path = None, prefix = None, version = None, create = True):

        self.path    = path or module_path('rdvhome', 'data')
        self.prefix  = prefix
        self.version = version

        if create:
            try:
                os.makedirs(self.path)
            except FileExistsError:
                pass

    def path_for_key(self, key, prefix = None, version = None):
        return os.path.join(
            self.path, '-'.join(filter(None, (
                prefix or self.prefix,
                str(key),
                version or self.version
            ))) + self.extension
        )

    def get(self, key, default = None, **opts):
        try:
            with open(self.path_for_key(key, **opts)) as f:
                return self.encoder.load(f)
        except FileNotFoundError:
            return default

    def set(self, key, value, **opts):
        with open(self.path_for_key(key, **opts), 'w') as f:
            self.encoder.dump(value, f)