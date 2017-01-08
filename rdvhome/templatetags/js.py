# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.contrib.staticfiles.finders import find
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

@register.simple_tag
def inline_js(path = 'js/mqttws31.min.js'):
    with open(find(path), 'r') as f:
        return mark_safe(f.read())