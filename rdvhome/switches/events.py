

from aioreactive.core import AsyncAnonymousObserver, AsyncStream, subscribe as _subscribe

import asyncio
import traceback

class EventStream(AsyncStream):

    def subscribe(self, func):
        return subscribe(self, func)

    async def start(self):
        pass

    async def watch(self):
        pass


def subscribe(observable, func):
    return _subscribe(observable, AsyncAnonymousObserver(func))