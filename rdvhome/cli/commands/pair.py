from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.homekit import driver

from rpy.cli.utils import SimpleCommand

class Command(SimpleCommand):

    help = "Pair homekit"

    def handle(self, **opts):

        driver.accessory.setup_message()