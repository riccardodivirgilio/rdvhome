# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from functools import reduce

import six

def first(iterable, default = None):
    try:
        return next(iter(iterable))
    except StopIteration:
        return default

def last(iterable, default = None):
    try:
        return iterable[-1]
    except IndexError:
        return default

def identity(x):
    return x

def is_iterable(obj, exclude_list = six.string_types):
    if isinstance(obj, exclude_list):
        return False
    return hasattr(obj, '__iter__')

def iterate(*args):
    for arg in args:
        if not is_iterable(arg):
            yield arg
        else:
            yield from arg

def composition(*functions):

    if not functions:
        return identity

    if len(functions) == 1:
        return first(functions)

    return reduce(
        lambda f, g: lambda *args, **kw: f(g(*args, **kw)),
        reversed(functions)
    )