# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.baseconv import base64 as encoder

class Toggle(object):

    def __init__(self, id, name = None, alias = []):
        self.id = id
        self.name = name
        self.alias = alias
        self.order = encoder.decode(id)

        self.backend = None

    def set_backend(self, backend):
        self.backend = backend
        return self

    def serialize(self):
        on = self.get_status()
        return dict(
            on = on,
            name = self.name,
            order = self.order,
            action = reverse(
                'toggle',
                kwargs = {'mode': not on, 'number': self.id}
            ),
        )

    def switch(self, status = None):
        return self.backend.switch([self], status = status)

    def get_status(self):
        return self.backend.get_status([self])

    def set_status(self, status = True):
        return self.backend.set_status([self])

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class ToggleList(object):

    def __init__(self, toggles):
        self.toggles = [
            toggle.set_backend(self)
            for toggle in toggles
        ]

    def serialize(self):
        return OrderedDict(
            (toggle.id, toggle.serialize())
            for toggle in self
        )

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.__class__(*filter(lambda toggle: toggle.id == func, self))
        if isinstance(func, (list, tuple, dict)):
            return self.__class__(*filter(lambda toggle: toggle.id in func, self))
        return self.__class__(*filter(func, self))

    def switch(self, *args, **kw):
        return [toggle.switch(*args, **kw) for toggle in self]

    def __bool__(self):
        return bool(self.toggles)

    def __len__(self):
        return len(self.toggles)

    def __iter__(self):
        return iter(self.toggles)

    def __repr__(self):
        return repr(self.toggles)