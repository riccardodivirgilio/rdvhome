# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.events import status_stream

import asyncio

async def log(value):
    print(value)

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
            status_stream.subscribe(log)
        )

        print('Server started at http://%s:%s' % (address, port))

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass