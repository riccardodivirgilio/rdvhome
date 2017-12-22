# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import sys

class SimpleCommand(object):

    help = None

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

def require_django_setup(func):
    def func_wrapper(*args, **kw):

        from django.conf import settings

        if not getattr(settings, 'django_setup_done', False):
            from django import setup
            setup()
            settings.django_setup_done = True

        return func(*args, **kw)
    return func_wrapper