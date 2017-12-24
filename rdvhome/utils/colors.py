# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from colour import Color

import math

def to_color(spec):
    if isinstance(spec, Color):
        return spec
    return Color(spec)

def hsb_to_hsl(h, s, b):
    l = 0.5 * b  * (2 - s)
    s = b * s / (1 - math.fabs(2*l-1))
    return Color(
        hue        = h,
        saturation = s,
        luminance  = l,
    )