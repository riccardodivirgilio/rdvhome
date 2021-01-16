from __future__ import absolute_import, print_function, unicode_literals

from colour import Color

from rpy.functions.datastructures import data
from rpy.functions.decorators import to_data
from rpy.functions.functional import identity

import math
import random

PHILIPS_RANGE = data(hue=65535, saturation=254, brightness=254)
HOMEKIT_RANGE = data(hue=360, saturation=100, brightness=100)

class HSB(object):
    def __init__(self, hue=None, saturation=None, brightness=None, **opts):
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

    @to_data
    def serialize(self, full=False):
        for attr in ("hue", "saturation", "brightness"):
            if full or (getattr(self, attr) is not None):
                yield attr, getattr(self, attr) or 0

    def __eq__(self, other):
        return isinstance(other, HSB) and all(
            round(getattr(self, attr), 2) == round(getattr(other, attr), 2)
            for attr in ("hue", "saturation", "brightness")
        )

    def __repr__(self):
        return "<HSB h=%(hue)s s=%(saturation)s b=%(brightness)s>" % self.serialize(full=True)

    def __bool__(self):
        return bool(self.serialize())

def philips_to_color(color_range=PHILIPS_RANGE, **opts):
    return HSB(
        **{
            attr: opts[attr] / const
            for attr, const in color_range.items()
            if opts.get(attr, None) is not None
        }
    )

@to_data
def color_to_philips(color, color_range=PHILIPS_RANGE, key_function=lambda attr: attr[0:3]):
    color = to_color(color)
    for attr, const in color_range.items():
        if getattr(color, attr) is not None:
            yield key_function(attr), int(getattr(color, attr) * const)

def homekit_to_color(color_range=HOMEKIT_RANGE, **opts):
    return philips_to_color(**opts, color_range=color_range)

def color_to_nanoleaf(color, color_range=HOMEKIT_RANGE):
    return color_to_philips(
        color,
        color_range=color_range,
        key_function=lambda key: key == "saturation" and "sat" or key,
    )

def color_to_homekit(color, color_range=HOMEKIT_RANGE):
    return color_to_philips(color, color_range=color_range, key_function=identity)

def to_color(spec=None):
    if isinstance(spec, HSB):
        return spec
    if isinstance(spec, dict):
        return HSB(**spec)
    if isinstance(spec, Color):
        return HSB(*hsl_to_hsb(spec.hue, spec.saturation, spec.luminance))
    elif spec:
        return to_color(Color(spec))
    else:
        return HSB()

def hsb_to_hsl(h, s, b):
    l = 0.5 * b * (2 - s)
    try:
        s = b * s / (1 - math.fabs(2 * l - 1))
        return h, s, l
    except ZeroDivisionError:
        return h, 1, l

def hsl_to_hsb(h, s, l):
    b = (2 * l + s * (1 - math.fabs(2 * l - 1))) / 2
    s = 2 * (b - l) / b
    return h, s, b

def hsb_to_color(h, s, b):
    h, s, l = hsb_to_hsl(h, s, b)
    return Color(hue=h, saturation=s, luminance=l)

def random_color():
    return HSB(hue=random.random(), saturation=0.5 + random.random() * 0.5)