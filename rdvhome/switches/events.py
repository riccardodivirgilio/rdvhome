

from aioreactive.core import AsyncAnonymousObserver, AsyncStream, subscribe as _subscribe

import asyncio
import traceback

import aiohttp
import itertools
import asyncio



async def periodic_task(func, interval, **opts):
    for i in itertools.count():
        asyncio.create_task(func(i,  **opts))

        if callable(interval):
            await asyncio.sleep(interval(i))
        else:
            await asyncio.sleep(interval)

class EventStream(AsyncStream):

    def subscribe(self, func):
        return subscribe(self, func)

    async def start(self):
        pass

    async def watch(self):
        pass

    async def create_periodic_task(self, func, **opts):
        asyncio.create_task(periodic_task(func, **opts))

def subscribe(observable, func):
    return _subscribe(observable, AsyncAnonymousObserver(func))