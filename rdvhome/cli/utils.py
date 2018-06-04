# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.decorators import to_data
from rdvhome.utils.importutils import module_path

import argparse
import os
import sys

@to_data
def discover_with_convention(modules, import_name):
    for module in modules:
        for filename in os.listdir(module_path(module)):
            basename, ext = os.path.splitext(filename)
            if ext == '.py' and not basename == '__init__':
                yield basename, '%s.%s.%s' % (module, basename, import_name)

class SimpleCommand(object):

    help  = None
    print = print

    def __init__(self, argv = None):
        self.argv = (argv or sys.argv[:])

    def create_parser(self):
        return argparse.ArgumentParser(description=self.help)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **opts):
        pass

    def main(self):
        parser = self.create_parser()
        if parser:
            self.add_arguments(parser)

            cmd_options = vars(parser.parse_args(self.argv[1:]))
            args = cmd_options.pop('args', ())
            return self.handle(*args, **cmd_options)

        return self.handle()