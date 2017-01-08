# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import url

from functools import partial

from rdvhome.api import api_response, output_switch, status_detail, status_list
from rdvhome.app import home

handler403 = partial(api_response, status = 403, message = "PermissionDenied")
handler404 = partial(api_response, status = 404, message = "PageNotFound")
handler500 = partial(api_response, status = 500, message = "InternalServerError")

urlpatterns = [
    url(r'^$', home),
    url(r'^switch$', status_list, name = "status"),
    url(r'^switch/(?P<number>[a-zA-Z0-9-]+)$', status_detail, name = "status"),
    url(r'^switch/(?P<number>[a-zA-Z0-9-]+)/on$', output_switch, kwargs = {'mode': True}, name = 'toggle'),
    url(r'^switch/(?P<number>[a-zA-Z0-9-]+)/off$', output_switch, kwargs = {'mode': False}, name = 'toggle'),
    url(r'^switch/(?P<number>[a-zA-Z0-9-]+)/toggle$', output_switch, kwargs = {'mode': None}, name = 'toggle'),
]