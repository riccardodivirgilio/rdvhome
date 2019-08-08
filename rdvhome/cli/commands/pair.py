# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.cli.utils import SimpleCommand

from rdvhome.homekit import driver


class Command(SimpleCommand):

    help = 'Pair homekit'


    def handle(self, **opts):

        driver.accessory.setup_message()
