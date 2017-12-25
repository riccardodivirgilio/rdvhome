# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.switches import switches
from rdvhome.switches.events import EventStream, subscribe
from rdvhome.utils.async import run_all
from rdvhome.utils.process import system_open
from aiohttp import web

import asyncio

async def log(event):
    print(event.id, event.get('on', None) and 'on' or 'off', event.get('color', None) or '')

class Command(SimpleCommand):

    help = 'Run the home app'

    def add_arguments(self, parser):
        pass

    def handle(self, port = settings.SERVER_PORT, address = settings.SERVER_ADDRESS):

        if settings.DEBUG:
            import aiohttp_autoreload
            aiohttp_autoreload.start()

        run_all(switches.subscribe(log))

        system_open('http://%s:%s' % (address, port))

        web.run_app(app, port=port)
        