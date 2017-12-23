# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand

import asyncio

class Command(SimpleCommand):

    help = 'Run the home app'

    def add_arguments(self, parser):
        pass

    def handle(self, port = 8500, debug = True):

        if debug:
            import aiohttp_autoreload
            aiohttp_autoreload.start()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            loop.create_server(
                app.make_handler(),
                '0.0.0.0',
                port
            )
        )

        print('Server started at http://0.0.0.0:%s' % port)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
