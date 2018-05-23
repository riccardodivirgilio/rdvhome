# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand

class Command(SimpleCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):

        from rdvhome import fabfile

        from fabric.main import load_fabfile
        from fabric.api import execute
        from fabric import state

        docstring, callables, default = load_fabfile(fabfile.__file__)
        state.commands.update(callables)

        def to_func(f):
            if f in callables:
                return (f, ())

        functions = None
        to_execute = True

        if not args and default:
            functions = [default.name]
        elif args:
            functions = tuple(
                filter(
                    None, [
                        to_func(func)
                        for func in args
                    ]
                )
            )

        if to_execute and functions:
            for func, args in functions:
                execute(func, *args)

        else:

            self.print("Available fabric:")
            for command in sorted(callables.keys()):
                self.print(" - %s" % command)