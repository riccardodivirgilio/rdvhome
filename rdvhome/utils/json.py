

from colour import Color

from rdvhome.utils.colors import HSB, to_color

from rpy.functions.datastructures import data

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
        elif isinstance(obj, (set, frozenset, types.GeneratorType)):
            return tuple(obj)
        elif hasattr(obj, 'serialize'):
            return obj.serialize()
        else:
            return json.JSONEncoder.default(self, obj)

def dump(obj, f, indent=4):
    return json.dump(obj, f, indent=indent, cls=JSONEncoder)

def load(f, indent=4):
    return json.load(f, object_hook=data)

def dumps(obj, indent=4):
    return json.dumps(obj, indent=indent, cls=JSONEncoder)

def loads(obj):
    return json.loads(obj, object_hook=data)