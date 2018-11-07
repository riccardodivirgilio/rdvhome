# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.utils.async import syncronous_wait_all, wait_all
from rdvhome.utils.functional import iterate
from rdvhome.utils.gpio import get_gpio

import asyncio
import random

import asyncio
import websockets
import json
import time
import sys 

#https://github.com/krzynio/python-samsung-smarttv-2016
#http://www.maartenvisscher.nl/samsung-tv-control/javadoc/nl/maartenvisscher/samsungtvcontrol/Keycode.html

#https://github.com/Ape/samsungctl

#https://github.com/Ape/samsungctl/issues/75

#to start an app http://192.168.1.227:8001/ws/apps/Netflix in POST

#https://review.tizen.org/git/?p=platform/core/convergence/app-comm-svc.git;a=blob;f=MSF-Node/org.tizen.multiscreen/server/plugins/plugin-api-v2/index.js;h=0e7cfd5c769beef98c3fab1cc98e52b7196d6380;hb=refs/heads/tizen_3.0

#https://developer.samsung.com/tv/develop/legacy-platform-library/ref00003/Client_(HHP)_to_TV_Application_Communication#Application-Methods

# possible solution
# pool every 5 sec this http://192.168.1.227:8001/ws/apps/, is not going to reply if the screen is off after 30 sec

async def _remote(tv_addr, keys,delay=1):
    websocket = await websockets.connect('ws://%s:%d/api/v2/channels/samsung.remote.control' % (tv_addr,8001))
    if type(keys) is str:
        _keys = [keys]
    else:
        _keys = keys

    try:

        async for message in websocket:
            print(message)
            parsed = json.loads(message)



            if (parsed['event'] == 'ms.channel.connect'):  

                k = 0
                for key in _keys:
                    k = k + 1
                    cmd = '{"method":"ms.remote.control","params":{"Cmd":"Click","DataOfCmd":"%s","Option":"false","TypeOfRemote":"SendRemoteKey"}}' % key
                    print(await websocket.send(cmd))
                    if k != len(_keys):
                        await asyncio.sleep(delay)     

                
    except asyncio.CancelledError:
        await websocket.close()


if __name__ == "__main__":
    remote(sys.argv[1], sys.argv[2:])

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):

        syncronous_wait_all(
            _remote(
                '192.168.1.227', 
                #['KEY_POWER']
                ['KEY_0']
            )
        )