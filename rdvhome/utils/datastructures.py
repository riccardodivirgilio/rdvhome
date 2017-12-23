# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

class data(dict):

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))

    def __setattr__(self, attr, value):
        return self.__setitem__(attr, value)

    def __delattr__(self, attr):
        return self.__delattr__(attr)