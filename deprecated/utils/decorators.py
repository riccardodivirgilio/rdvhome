# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from workflow.utils.functional import composition

def apply(*func):
    comp = composition(*func)
    def multipass(fn):
        def caller(*args, **opts):
            return comp(fn(*args, **opts))
        return caller
    return multipass

to_tuple           = apply(tuple)
to_dict            = apply(dict)
delete_duplicates  = apply(lambda res: tuple(OrderedDict.fromkeys(res)))