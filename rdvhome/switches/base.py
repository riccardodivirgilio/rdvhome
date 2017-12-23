# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.baseconv import base64 as encoder

from rdvhome.utils.functional import first

class Switch(object):

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
                'switch',
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

class SwitchList(object):

    def __init__(self, switches):
        self.switches = tuple(
            switch.set_backend(self)
            for switch in switches
        )

    def serialize(self):
        return OrderedDict(
            (switch.id, switch.serialize())
            for switch in self
        )

    def get(self, pk):
        for obj in self:
            if obj.id == pk:
                return obj

    def copy(self, *args, **opts):
        return self.__class__(*args, **opts)

    def filter(self, func = None):
        if isinstance(func, six.string_types):
            return self.copy(filter(lambda switch: func in switch.alias(), self))
        if isinstance(func, (list, tuple, dict)):
            return self.copy(filter(lambda switch: any(f in switch.alias() for f in func), self))
        if isinstance(func, Switch):
            return self.copy([func])
        return self.copy(filter(func, self))

    def switch(self, status = None):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError

    def __bool__(self):
        return bool(self.switches)

    def __len__(self):
        return len(self.switches)

    def __iter__(self):
        return iter(self.switches)

    def __repr__(self):
        return repr(self.switches)