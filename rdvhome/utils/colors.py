# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from colour import Color

import math

def to_color(spec):
    if isinstance(spec, Color):
        return spec
    elif spec:
        return Color(spec)

def hsb_to_hsl(h, s, b):
    l = 0.5 * b  * (2 - s)
    s = b * s / (1 - math.fabs(2*l-1))
    return h, s, l

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