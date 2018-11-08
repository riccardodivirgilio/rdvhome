# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.cli.dispatch import DispatchCommand as _DispatchCommand


class DispatchCommand(_DispatchCommand):

    modules = ['rdvhome.cli.commands']
