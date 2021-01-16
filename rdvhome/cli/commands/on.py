from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.api import switch

from rpy.cli.utils import SimpleCommand
from rpy.functions.asyncio import syncronous_wait_all

class Command(SimpleCommand):

    help = "Switch on the lights"

    def add_arguments(self, parser):
        parser.add_argument("args", nargs="*")

    def handle(self, *args):
        for r in syncronous_wait_all(switch(args or "default", on=True)):
            print("on:", *sorted(r.switches.keys()))