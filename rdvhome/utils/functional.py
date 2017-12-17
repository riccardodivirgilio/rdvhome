# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.files.base import File
from django.http import HttpResponse
from django.utils import six

from functools import reduce

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

def is_iterable(obj, exclude_list = six.string_types + (File, HttpResponse)):
    if isinstance(obj, exclude_list):
        return False
    return hasattr(obj, '__iter__')

def to_iterable(obj):
    if not is_iterable(obj):
        return (obj, )
    return obj

def composition(*functions):

    if not functions:
        return identity

    if len(functions) == 1:
        return first(functions)

    return reduce(
        lambda f, g: lambda *args, **kw: f(g(*args, **kw)),
        reversed(functions)
    )