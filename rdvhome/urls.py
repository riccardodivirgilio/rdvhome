# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from functools import partial

from rdvhome.views import api_response, home_view, input_view, output_switch, output_view

handler403 = partial(api_response, status = 403, message = "PermissionDenied")
handler404 = partial(api_response, status = 404, message = "PageNotFound")
handler500 = partial(api_response, status = 500, message = "InternalServerError")

urlpatterns = [
    url(r'^$', home_view),
    url(r'^input/(?P<number>[0-9]{1,2})$', input_view),
    url(r'^output/(?P<number>[0-9]{1,2})$', output_view),
    url(r'^output/(?P<number>[0-9]{1,2})/on$', partial(output_switch, mode = True)),
    url(r'^output/(?P<number>[0-9]{1,2})/off$', partial(output_switch, mode = False)),
]