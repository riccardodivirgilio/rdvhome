from __future__ import absolute_import, print_function, unicode_literals

from aioreactive.core import AsyncAnonymousObserver, AsyncStream, subscribe as _subscribe

import asyncio
import traceback

class EventStream(AsyncStream):

    interval = None

    def subscribe(self, func):
        return subscribe(self, func)

    async def start(self):
        pass

    async def watch(self):

        while self.interval:
            try:
                await self.periodic_task()
            except Exception as e:
                print(e)
                traceback.print_tb(e.__traceback__)

            await asyncio.sleep(self.interval)

    async def periodic_task(self):
        pass

def subscribe(observable, func):
    return _subscribe(observable, AsyncAnonymousObserver(func))