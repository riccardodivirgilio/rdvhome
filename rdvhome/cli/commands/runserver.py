# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from rdvhome.app import app
from rdvhome.cli.utils import SimpleCommand

class Command(SimpleCommand):

    help = 'Run the home app'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        web.run_app(app, port = 8500)