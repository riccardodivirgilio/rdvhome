# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.http import Http404, JsonResponse

from rdvhome.gpio import get_input, set_output, IN, OUT, PINS

def status_verbose(mode = None):
    return mode and "on" or "off"

def api_response(request = None, status_code = 200, message = "OK", **kw):
    return JsonResponse(
        dict(
            kw,
            code = status_code,
            success = status_code == 200,
            message = message
        ),
        status = status_code,
        json_dumps_params = {"indent": 4}
    )

def status_view(request):
    return api_response(
        gpio = {
            pin: status_verbose(get_input(pin))
            for pin, mode in PINS.items()
            if mode is OUT
        },
    )

def validate_pin(number, mode):
    n = int(number)
    if not PINS.get(n, None) is mode:
        raise Http404("Invalid pin number %s" % n)
    return n

def output_view(request, number):
    pin = validate_pin(number, OUT)
    return api_response(
        gpio = pin,
        mode = "output",
        status = status_verbose(get_input(pin))
    )

def output_switch(request, number, mode = True):
    pin = validate_pin(number, OUT)
    set_output(pin, mode)
    return api_response(
        gpio = pin,
        mode = "output",
        status = status_verbose(mode)
    )