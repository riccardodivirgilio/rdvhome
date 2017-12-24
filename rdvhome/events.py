# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aioreactive.core import AsyncAnonymousObserver, AsyncStream, subscribe
from rdvhome.utils.async import run_all

import asyncio

class EventStream(AsyncStream):

    def subscribe(self, func):
        return subscribe(status_stream, AsyncAnonymousObserver(func))

    def send(self, event):
        run_all(self.asend(event))
        return event

status_stream = EventStream()