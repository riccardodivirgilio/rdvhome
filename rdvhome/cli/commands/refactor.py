# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.cli.commands.refactor import Command as RefactorCommand


class Command(RefactorCommand):
    modules = ["rdvhome"]
