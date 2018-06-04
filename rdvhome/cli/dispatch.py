# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import discover_with_convention, SimpleCommand
from rdvhome.utils.functional import first
from rdvhome.utils.importutils import import_string

import sys

class DispatchCommand(SimpleCommand):

    modules = ['rdvhome.cli.commands']
    class_name = 'Command'

    default_command = None

    def subcommands(self):
        return discover_with_convention(self.modules, self.class_name)

    def handle(self, attr = None):
        all_commands = self.subcommands()

        if attr is None and self.default_command:
            attr = self.default_command

        if attr in all_commands:
            return import_string(all_commands[attr])(self.subcommand_args()).main()

        self.print('Select one of the following commands:')
        for command in sorted(all_commands.keys()):
            self.print(' -', command)

        sys.exit(1)

    def subcommand_args(self):
        argv = list(self.argv)
        if len(argv) > 1:
            argv.pop(1)
        return argv

    def main(self):
        if len(self.argv) > 1 and self.argv[1]:
            return self.handle(self.argv[1])
        return self.handle()