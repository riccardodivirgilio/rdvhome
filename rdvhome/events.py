# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aioreactive.core import AsyncStream, subscribe, AsyncAnonymousObserver
import asyncio

class EventStream(AsyncStream):

    def subscribe(self, func):
        return subscribe(status_stream, AsyncAnonymousObserver(func))

    def send(self, *args, **opts):
        return asyncio.ensure_future(self.asend(*args, **opts))

status_stream = EventStream()