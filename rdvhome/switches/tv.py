# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio

import aiohttp
import websockets
from rpy.functions.functional import iterate

from rdvhome.switches.base import Switch, capabilities
from rdvhome.utils import json


async def send_commands(tv_addr, keys):
    try:
        websocket = await websockets.connect(
            "ws://%s:%d/api/v2/channels/samsung.remote.control" % (tv_addr, 8001)
        )
        async for message in websocket:
            parsed = json.loads(message)
            if parsed["event"] == "ms.channel.connect":
                for key in iterate(keys):
                    cmd = (
                        '{"method":"ms.remote.control","params":{"Cmd":"Click","DataOfCmd":"%s","Option":"false","TypeOfRemote":"SendRemoteKey"}}'
                        % key
                    )
                    await websocket.send(cmd)
                break

    except asyncio.CancelledError:
        await websocket.close()
    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print("ERROR", e)


class SamsungSmartTV(Switch):

    default_capabilities = capabilities()

    def __init__(self, id, ipaddress, **opts):

        self.ipaddress = ipaddress
        self.on = False

        super().__init__(id, **opts)

    async def status(self):
        return await self.send(on=self.on, allow_on=self.on)

    async def _check_on(self, timeout=1):
        try:
            async with aiohttp.ClientSession(
                read_timeout=timeout, conn_timeout=timeout
            ) as session:
                async with session.get(
                    "http://%s:8001/api/v2/" % self.ipaddress
                ) as response:
                    return True
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            print(e)

    async def switch(self, on=None, **opts):
        if not on == self.on:
            if not on and await self._check_on():
                await send_commands(self.ipaddress, "KEY_POWER")
            self.on = on
        return await self.send(on=self.on, allow_on=self.on)

    async def watch(self, pool_every=15, **opts):

        while True:
            on = await self._check_on(**opts)
            if not on == self.on:
                self.on = on
                await self.send(on=self.on, allow_on=self.on)

            await asyncio.sleep(pool_every)
