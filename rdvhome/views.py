# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.http import Http404, JsonResponse

from rdvhome.gpio import GPIO, IN, OUT, PINS

def api_response(status = 200, message = "OK", **kw):
    return JsonResponse(
        dict(
            kw,
            status = status,
            success = status == 200,
            message = message
        ),
        status = status,
        json_dumps_params = {"indent": 4}
    )

def home_view(request):
    return api_response(
        success = True,
        input = [
            pin
            for pin, mode in PINS.items()
            if mode is IN
        ],
        output = [
            pin
            for pin, mode in PINS.items()
            if mode is OUT
        ],
    )

def validate_pin(number, mode):
    n = int(number)
    if not PINS.get(n, None) is mode:
        raise Http404("Invalid pin number %s" % n)
    return n

def output_view(request, number):
    pin = validate_pin(number, OUT)
    return api_response(
        pin = pin
    )

def input_view(request, number):
    pin = validate_pin(number, IN)
    return api_response(
        pin = pin,
        mode = "input"
    )

def output_view(request, number):
    pin = validate_pin(number, OUT)
    if GPIO:
        mode = bool(GPIO.input(pin))
    else:
        mode = "unknown"
    return api_response(
        pin = pin,
        mode = "output",
        on = mode
    )

def output_switch(request, number, mode = True):
    pin = validate_pin(number, OUT)
    if GPIO:
        GPIO.output(pin, mode)
    return api_response(
        pin = pin,
        mode = "output",
        on = mode
    )