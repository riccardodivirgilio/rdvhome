# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio

from rpy.functions.datastructures import data

loop = asyncio.get_event_loop()

settings = data(
    DEBUG=False,
    SERVER_PORT=8500,
    SERVER_ADDRESS="0.0.0.0",
    SWITCHES={},
    INSTALL_DEPENDENCIES=False,
    DEPENDENCIES={
        "aiohttp": "2.3.5",
        #'aiofiles': '0.3.2',
        #"fabric3": "1.13.1.post1",
        #'hap-python': None,
        "aiohttp-autoreload": None,
        "aioreactive": None,
        "asyncio": None,
        "colour": None,
        "django": None,
        "six": None,
        "yarl": "0.18.0",
        "base36": None,
        "pyqrcode": None,
        "hap-python": None,
        "python-rpy": "1.0.17",
        "websockets": None,
    },
)
