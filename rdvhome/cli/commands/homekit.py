# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import signal

from aiohttp import web
from rpy.cli.utils import SimpleCommand
from rpy.functions.asyncio import run_all
from rpy.functions.importutils import module_path
from rpy.functions.process import system_open

from rdvhome.app import app
from rdvhome.conf import settings
from rdvhome.homekit import driver
from rdvhome.switches import switches
from rdvhome.utils.json import dumps



class Command(SimpleCommand):

    help = "Run homekit"

    def handle(
        self,
    ):

        driver.accessory.setup_message()
        print("TO CONNECT TO HOMEKIT USE: %s" % driver.state.pincode.decode())
        driver.start()
