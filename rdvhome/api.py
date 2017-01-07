# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.http import Http404, JsonResponse

from rdvhome.encoding import JSONEncoder
from rdvhome.gpio import get_input, set_output
from rdvhome.toggles import local_toggles

def status_verbose(mode = None):
    return mode and "on" or "off"

def api_response(request = None, status_code = 200, **kw):
    return JsonResponse(
        dict(
            kw,
            code = status_code,
            success = status_code == 200,
        ),
        status = status_code,
        encoder = JSONEncoder,
        json_dumps_params = {"indent": 4}
    )

def status_list(request):
    return api_response(mode = "status", toggles = local_toggles)

def status_detail(request, number):
    toggles = local_toggles.filter(number)
    return api_response(
        mode = "status",
        toggles = toggles,
        status_code = toggles and 200 or 404
    )

def output_switch(request, number, mode = True):
    toggles = local_toggles.filter(number)
    #if mode is None:
    #    mode = not get_input(pin)
    #set_output(pin, mode)
    return api_response(
        mode = "status",
        toggles = toggles,
        status_code = toggles and 200 or 404
    )