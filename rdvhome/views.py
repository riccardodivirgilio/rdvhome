# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.http import Http404, JsonResponse

from rdvhome.gpio import GPIO, IN, OUT, PINS

def status(pin):
    if GPIO:
        return bool(GPIO.input(pin)) and "on" or "off"
    else:
        return "unknown"    

def api_response(request = None, status = 200, message = "OK", **kw):
    return JsonResponse(
        dict(
            kw,
            code = status,
            success = status == 200,
            message = message
        ),
        status = status,
        json_dumps_params = {"indent": 4}
    )

def home_view(request):
    return api_response(
        input = {
            pin: status(pin)
            for pin, mode in PINS.items()
            if mode is IN
        },
        output = {
            pin: status(pin)
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
    return api_response(
        pin = pin,
        mode = "output",
        status = status(pin)
    )

def output_switch(request, number, mode = True):
    pin = validate_pin(number, OUT)
    if GPIO:
        GPIO.output(pin, mode)
    return api_response(
        pin = pin,
        mode = "output",
        status = mode
    )