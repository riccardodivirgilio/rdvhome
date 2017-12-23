# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches.base import Switch, SwitchList
from rdvhome.utils.datastructures import data

import datetime
import decimal
import json
import types

class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, (Switch, SwitchList)):
            return obj.serialize()
        elif isinstance(obj, (set, frozenset, types.GeneratorType)):
            return tuple(obj)
        else:
            return json.JSONEncoder.default(self, obj)

def dumps(obj, indent = 4):
    return json.dumps(obj, indent = indent, cls = JSONEncoder)

def loads(obj):
    return json.loads(obj, object_hook = data)
