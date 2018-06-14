# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.datastructures import data
from rdvhome.utils.functional import composition
import time
def decorate(*func):
    comp = composition(*func)
    def multipass(fn):
        def caller(*args, **opts):
            return comp(fn(*args, **opts))
        return caller
    return multipass

to_tuple = decorate(tuple)
to_data  = decorate(data)

def debounce(s):
    """Decorator ensures function that can only be called once every `s` seconds.
    """
    def decorate(f):
        t = None

        def wrapped(*args, **kwargs):
            nonlocal t
            t_ = time.time()
            if t is None or t_ - t >= s:
                result = f(*args, **kwargs)
                t = time.time()
                return result
        return wrapped
    return decorate