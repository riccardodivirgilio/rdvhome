# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.baseconv import base64 as encoder

from rdvhome.utils.functional import first

class Toggle(object):

    def __init__(self, id, name = None, alias = []):
        self.id = id
        self.name = name
        self.order = encoder.decode(id)

        self.backend = None
        self._alias = alias

    def alias(self):
        yield self.id
        yield 'all'
        yield from self.alias

    def set_backend(self, backend):
        self.backend = backend
        return self

    def serialize(self):
        status = self.get_status()
        status.update(dict(
            name = self.name,
            order = self.order,
            action = reverse(
                'toggle',
                kwargs = {'mode': not status['on'], 'number': self.id}
            ),
        ))
        return status

    def switch(self, status = None):
        return first(self.backend.filter(self).switch(status = status).values())

    def get_status(self):
        return first(self.backend.filter(self).get_status().values())

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

class ToggleList(object):

    def __init__(self, toggles):
        self.toggles = tuple(
            toggle.set_backend(self)
            for toggle in toggles
        )

    def serialize(self):
        return OrderedDict(
            (toggle.id, toggle.serialize())
            for toggle in self
        )

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda toggle: func in toggle.alias(), self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(filter(lambda toggle: any(f in toggle.alias() for f in func), self))
        if isinstance(func, Toggle):
            return self.copy([func])
        return self.copy(filter(func, self))

    def switch(self, status = None):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError

    def __bool__(self):
        return bool(self.toggles)

    def __len__(self):
        return len(self.toggles)

    def __iter__(self):
        return iter(self.toggles)

    def __repr__(self):
        return repr(self.toggles)

class ToggleCollection(ToggleList):

    def __init__(self, collections):
        self.collections = tuple(filter(None, collections))

    def filter(self, *args, **opts):
        return self.copy(
            collection.filter(*args, **opts)
            for collection in self.collections
        )

    def switch(self, status = None):
        d = {}
        for collection in self.collections:
            d.update(collection.switch(status))
        return d

    def __bool__(self):
        return any(map(bool, self.collections))

    def __len__(self):
        return sum(map(len, self.collections))

    def __iter__(self):
        for collection in self.collections:
            yield from collection

    def __repr__(self):
        return '<ToggleCollection: %s>' % len(self)