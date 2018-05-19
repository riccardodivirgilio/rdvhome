# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.datastructures import data

settings = data(
    DEBUG          = False,
    SERVER_PORT    = 8500,
    SERVER_ADDRESS = '0.0.0.0',
    SWITCHES       = {},
    INSTALL_DEPENDENCIES = False,
    DEPENDENCIES = {
        'aiohttp': '2.3.5',
        #'fabric3': None,
        'aiohttp-autoreload': None,
        'aioreactive': None,
        'asyncio': None,
        'colour':  None,
        'django':  None,
        'six':     None,
    }
)