# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from colour import Color

from rdvhome.utils.datastructures import data
from rdvhome.utils.decorators import to_data

import math
import random

PHILIPS_RANGE = data(
    hue        = 65535,
    saturation = 254,
    brightness = 254,
)

class HSB(object):

    def __init__(self, hue = None, saturation = None, brightness = None):
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

    @to_data
    def serialize(self, full = False):
        for attr in ['hue', 'saturation', 'brightness']:
            if full or (getattr(self, attr) is not None):
                yield attr, getattr(self, attr) or 0

    def __repr__(self):
        return '<HSB h=%(hue)s s=%(saturation)s b=%(brightness)s>' % self.serialize(full = True)

    def __bool__(self):
        return bool(self.serialize())

def philips_to_color(**opts):
    return HSB(**{
        attr: opts[attr] / const
        for attr, const in PHILIPS_RANGE.items()
        if opts.get(attr, None)
    })

@to_data
def color_to_philips(color):
    color = to_color(color)
    for attr, const in PHILIPS_RANGE.items():
        if getattr(color, attr) is not None:
            yield attr[0:3], int(getattr(color, attr) * const)

def to_color(spec):
    if isinstance(spec, HSB):
        return spec
    if isinstance(spec, dict):
        return HSB(**spec)
    if isinstance(spec, Color):
        return HSB(*hsl_to_hsb(spec.hue, spec.saturation, spec.luminance))
    elif spec:
        return to_color(Color(spec))

def hsb_to_hsl(h, s, b):
    l = 0.5 * b  * (2 - s)
    try:
        s = b * s / (1 - math.fabs(2*l-1))
        return h, s, l
    except ZeroDivisionError:
        return h, 1, l

def hsl_to_hsb(h, s, l):
    b = (2*l + s*(1-math.fabs(2*l-1)))/2
    s = 2*(b-l)/b
    return h, s, b

def hsb_to_color(h, s, b):
    h, s, l = hsb_to_hsl(h, s, b)
    return Color(
        hue        = h,
        saturation = s,
        luminance  = l,
    )

def random_color():
    return HSB(
        hue = random.random(), 
        saturation = 0.5 + random.random() * 0.5
    )