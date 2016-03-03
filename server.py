
from aiohttp import web, errors
import asyncio

from functools import partial

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

IN  = 1
OUT = 0

PINS = {
    10: OUT,
    12: IN,
    18: OUT,
}

if GPIO:
    GPIO.setmode(GPIO.BOARD)
    for n, mode in PINS.items():
        GPIO.setup(n, mode)

@asyncio.coroutine
def home_view(request):
    return web.json_response({
        "success": True, 
        "input": [
            pin
            for pin, mode in PINS.items()
            if mode is IN
        ],
        "output": [
            pin
            for pin, is_input in PINS.items()
            if mode is OUT
        ],
    })

def validate_pin(request, mode):
    n = int(request.match_info['number'])
    if not PINS.get(n, None) is mode:
        raise errors.HttpBadRequest("Invalid pin number")
    return n

@asyncio.coroutine
def output_view(request):
    pin = validate_pin(request, OUT)
    return web.json_response({
        "success": True, 
        "pin": pin
        })

@asyncio.coroutine
def input_view(request):
    pin = validate_pin(request, IN)
    return web.json_response({
        "success": True, 
        "pin": pin,
        "mode": "output"
        })

@asyncio.coroutine
def output_view(request):
    pin = validate_pin(request, OUT)
    if GPIO:
        mode = bool(GPIO.input(pin))
    else:
        mode = "unknown"
    return web.json_response({
        "success": True, 
        "pin": pin,
        "mode": "output",
        "on": mode
        })

@asyncio.coroutine
def output_switch(request, mode = True):
    pin = validate_pin(request, OUT)
    if GPIO:
        GPIO.output(pin, mode)
    return web.json_response({
        "success": True, 
        "pin": pin,
        "mode": "output",
        "on": mode
        })

app = web.Application()
app.router.add_route('*', '/', home_view)
app.router.add_route('*', '/input/{number:\d+}', input_view)
app.router.add_route('*', '/output/{number:\d+}', output_view)
app.router.add_route('*', '/output/{number:\d+}/on', partial(output_switch, mode = True))
app.router.add_route('*', '/output/{number:\d+}/off', partial(output_switch, mode = False))

web.run_app(app)