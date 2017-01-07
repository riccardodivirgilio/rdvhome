# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.http import Http404, JsonResponse

from rdvhome.encoding import JSONEncoder
from rdvhome.gpio import get_input, set_output
from rdvhome.server import RASPBERRY
from rdvhome.toggles import toggles, ToggleList

def status_verbose(mode = None):
    return mode and "on" or "off"

def validate_pin(number):
    pin = toggles.get(number)
    if not pin:
        raise Http404("Invalid pin number %s" % number)
    return pin

def api_response(request = None, status_code = 200, message = "OK", **kw):
    return JsonResponse(
        dict(
            kw,
            code = status_code,
            success = status_code == 200,
            message = message
        ),
        status = status_code,
        encoder = JSONEncoder,
        json_dumps_params = {"indent": 4}
    )

def status_list(request):
    return api_response(mode = "status", toggles = toggles)

def status_detail(request, number):
    pin = validate_pin(number)
    return api_response(
        mode = "status",
        toggles = ToggleList(pin)
    )

def output_switch(request, number, mode = True):
    pin = validate_pin(number)
    if mode is None:
        mode = not get_input(pin)
    set_output(pin, mode)
    return api_response(
        mode = "status",
        toggles = ToggleList(pin)
    )