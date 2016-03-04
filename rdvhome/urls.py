# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from functools import partial

from rdvhome.api import api_response, output_switch, output_view, status_view
from rdvhome.app import home

handler403 = partial(api_response, status = 403, message = "PermissionDenied")
handler404 = partial(api_response, status = 404, message = "PageNotFound")
handler500 = partial(api_response, status = 500, message = "InternalServerError")

urlpatterns = [
    url(r'^$', home),
    url(r'^gpio$', status_view),
    url(r'^gpio/(?P<number>[0-9]{1,2})$', output_view),
    url(r'^gpio/(?P<number>[0-9]{1,2})/on$', partial(output_switch, mode = True)),
    url(r'^gpio/(?P<number>[0-9]{1,2})/off$', partial(output_switch, mode = False)),
]