# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.switches import switches
from rdvhome.utils.async import run_all
from rdvhome.utils.process import system_open

import signal

try:
    from rdvhome.homekit import driver
except ImportError:
    driver = None

async def log(event):
    print(event.id, event.get('on', None) and 'on' or 'off', event.get('color', None) or '')

class Command(SimpleCommand):

    help = 'Run the home app'

    def add_arguments(self, parser):
        parser.add_argument('--open', dest = 'auto_open', default = False, action = 'store_true')

    def handle(self, port = settings.SERVER_PORT, address = settings.SERVER_ADDRESS, auto_open = False):

        if settings.DEBUG:
            import aiohttp_autoreload
            aiohttp_autoreload.start()

        run_all(switches.subscribe(log))

        if auto_open:
            system_open('http://%s:%s' % (address, port))

        # We want SIGTERM (kill) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        signal.signal(signal.SIGTERM, driver.signal_handler)

        #code borrowed from pyhap
        try:
            if driver:
                driver.add_job(driver._do_start)
            web.run_app(app, port=port)
        except KeyboardInterrupt:
            if driver:
                driver.loop.call_soon_threadsafe(
                    driver.loop.create_task,
                    driver.async_stop()
                )
                driver.loop.run_forever()
        finally:
            if driver:
                driver.loop.close()