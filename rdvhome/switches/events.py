# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aioreactive.core import AsyncAnonymousObserver, AsyncStream, subscribe as _subscribe

from rdvhome.utils.async import run_all

class EventStream(AsyncStream):

    def subscribe(self, func):
        return subscribe(self, func)

    def send(self, event):
        run_all(self.asend(event))
        return event

def subscribe(observable, func):
    return _subscribe(observable, AsyncAnonymousObserver(func))