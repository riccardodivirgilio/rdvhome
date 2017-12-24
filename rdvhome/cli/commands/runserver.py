# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.switches import switches
from rdvhome.switches.events import EventStream, subscribe
from rdvhome.utils.async import run_all

import asyncio

async def log(event):
    print(event.id, event.get('on', None) and 'on' or 'off')

class Command(SimpleCommand):

    help = 'Run the home app'

    def add_arguments(self, parser):
        pass

    def handle(self, port = settings.SERVER_PORT, address = settings.SERVER_ADDRESS):

        if settings.DEBUG:
            import aiohttp_autoreload
            aiohttp_autoreload.start()

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            loop.create_server(
                app.make_handler(),
                address,
                port
            )
        )

        loop.run_until_complete(
            switches.subscribe(log)
        )

        print('Server started at http://%s:%s' % (address, port))

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass