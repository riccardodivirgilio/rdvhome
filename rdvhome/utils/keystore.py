# -*- coding: utf-8 -*-

import os
import json

class KeyStore(object):

    def __init__(self, path, prefix = None, version = None, create = True):
        self.path    = path
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
            ))) + '.json'
        )

    def get(self, key, default = None, **opts):
        try:
            with open(self.path_for_key(key, **opts)) as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    def set(self, key, value, **opts):
        with open(self.path_for_key(key, **opts), 'w') as f:
            json.dump(value, f)