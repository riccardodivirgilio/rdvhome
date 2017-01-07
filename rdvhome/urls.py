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
    url(r'^status$', status_list),
    url(r'^status/(?P<number>[a-zA-Z0-9-]+)$', status_detail),
    url(r'^status/(?P<number>[a-zA-Z0-9-]+)/on$', partial(output_switch, mode = True)),
    url(r'^status/(?P<number>[a-zA-Z0-9-]+)/off$', partial(output_switch, mode = False)),
    url(r'^status/(?P<number>[a-zA-Z0-9-]+)/toggle$', partial(output_switch, mode = None)),
]