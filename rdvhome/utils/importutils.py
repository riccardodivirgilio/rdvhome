# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from importlib import import_module

import os
import six

def module_path(module, *args):
    if isinstance(module, six.string_types):
        try:
            module = import_module(module)
        except ImportError:
            return None
    return os.path.join(
        os.path.dirname(os.path.realpath(module.__file__)),
        *args
    )

def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """

    if not isinstance(dotted_path, six.string_types):
        return dotted_path

    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        raise ImportError("%s doesn't look like a module path" % dotted_path)

    module = import_module(module_path)

    if class_name == '__module__':
        return module

    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name))