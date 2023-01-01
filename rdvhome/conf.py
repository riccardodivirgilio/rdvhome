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
)
