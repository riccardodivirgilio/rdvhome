

from rpy.cli.dispatch import DispatchCommand as _DispatchCommand

class DispatchCommand(_DispatchCommand):

    modules = ["rdvhome.cli.commands"]