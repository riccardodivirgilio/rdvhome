# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os

import aiofiles
from rpy.functions.importutils import module_path
from rdvhome.utils.persistence import data_path

from rdvhome.utils import json


class KeyStore(object):

    encoder = json
    extension = ".json"

    def __init__(self, path=None, prefix=None, version=None, create=True):

        self.path = path or data_path()
        self.prefix = prefix
        self.version = version

        if create:
            try:
                os.makedirs(self.path)
            except FileExistsError:
                pass

    def path_for_key(self, key, prefix=None, version=None):
        return os.path.join(
            self.path,
            "-".join(
                filter(None, (prefix or self.prefix, str(key), version or self.version))
            )
            + self.extension,
        )

    async def get(self, key, default=None, **opts):
        try:
            async with aiofiles.open(self.path_for_key(key, **opts), "r") as f:
                contents = await f.read()
                return self.encoder.loads(contents)
        except FileNotFoundError:
            return default

    async def set(self, key, value, **opts):
        with open(self.path_for_key(key, **opts), "w") as f:
            f.write(self.encoder.dumps(value))
            return value
