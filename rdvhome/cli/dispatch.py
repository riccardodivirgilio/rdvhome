# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.utils.functional import first
from rdvhome.utils.importutils import import_string

import sys

class DispatchCommand(SimpleCommand):

    subcommands = [
        'run',
        'on',
        'off',
    ]

    def subcommand_args(self):
        argv = self.argv[:]
        if len(self.argv) > 1:
            argv.pop(1)
        return argv

    def dispatch(self, attr = None):
        if not attr:
            attr = first(self.subcommands)

        if attr in self.subcommands:
            return import_string('rdvhome.cli.commands.%s.Command' % attr)(self.subcommand_args()).main()

        print('Select one of the following commands:')
        for command in self.subcommands:
            print(' -', command)
        sys.exit(1)

    def main(self):
        if len(self.argv) > 1 and self.argv[1]:
            return self.dispatch(self.argv[1])
        return self.dispatch()