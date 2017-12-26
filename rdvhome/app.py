# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web
from aiohttp.client import _RequestContextManager
from aiohttp.test_utils import make_mocked_request

from functools import partial

from operator import methodcaller

from rdvhome.api import api_response, status, switch
from rdvhome.conf import settings
from rdvhome.switches import switches
from rdvhome.utils.async import run_all
from rdvhome.utils.colors import HSB, to_color
from rdvhome.utils.decorators import to_data
from rdvhome.utils.importutils import module_path
from rdvhome.utils.json import dumps

import aiohttp
import asyncio
import logging
import sys
import traceback

class ClientError(Exception):
    pass

@web.middleware
async def server_error(request, handler):
    try:
        return await handler(request)

    except ClientError as e:
        return JsonResponse(api_response(status = 400, reason = str(e)))

    except Exception as e:

        logging.error(e, exc_info=True)

        if settings.DEBUG and not request.method == 'WS':

            from django.conf import global_settings, settings as django_settings

            if not django_settings.configured:
                django_settings.configure(global_settings)
                django_settings.USE_I18N = False

            from django.views.debug import ExceptionReporter

            reporter = ExceptionReporter(
                None,
                *sys.exc_info(),
                is_email = False,
            )

            return web.Response(
                text = reporter.get_traceback_html(),
                content_type = 'text/html',
                status = 500
            )

        return JsonResponse(api_response(status = 500))

app = web.Application(middlewares = [server_error])

def url(path, name, **opts):
    def inner(func):
        app.router.add_route('GET', path, func, name = name, **opts)
        app.router.add_route('WS',  path, func, name = '%s_ws' % name, **opts)
    return inner

def JsonResponse(data, status = None, **opts):
    return web.Response(
        text = dumps(data),
        status = status or data.status or 200,
        **opts
    )

APP = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>%(title)s</title>
  </head>
  <body>
    <div id="app"></div>
    <script>%(js)s</script>
  </body>
</html>"""

def validate_color(spec):
    if spec in (None, '-'):
        return None
    try:
        spec = int(spec)
    except ValueError:
        raise ClientError('spec is not an integer')

    if spec > 100 or spec < 0:
        raise ClientError('spec color too big')
    else:
        return spec / 100

@to_data
def validate(number = None, color = None, hue = None, saturation = None, brightness = None):
    if number:
        yield 'number', number

    if color:
        try:
            yield 'color', to_color(color)
        except ValueError:
            raise ClientError('invalid color')

    args = tuple(map(validate_color, (hue, saturation, brightness)))

    if any(arg is not None for arg in args):
        yield 'color', HSB(*args)

@url('/', name = 'home')
async def view_home(request):
    with open(module_path('rdvhome', 'frontend', 'dist', 'build.js'), 'r') as f:
        return web.Response(
            text = APP % dict(
                title = 'Home',
                js    = f.read()
            ),
            content_type = 'text/html'
        )

@url('/switch', name = "status-list")
async def view_status_list(request):
    return JsonResponse(await status(**validate(**request.match_info)))

@url('/switch/{number:[a-zA-Z-0-9]+}', name = "status")
async def view_status_list(request):
    return JsonResponse(await status(**validate(**request.match_info)))

@url('/switch/{number:[a-zA-Z-0-9]+}/on', name = "on")
async def view_status_list(request):
    return JsonResponse(await switch(**validate(**request.match_info), on = True))

@url('/switch/{number:[a-zA-Z-0-9]+}/color/{color:[a-zA-Z-0-9]+}', name = "color")
async def view_status_list(request):
    return JsonResponse(await switch(**validate(**request.match_info)))

@url('/switch/{number:[a-zA-Z-0-9]+}/hsb/{hue:(-|[0-9]+)}/{saturation:(-|[0-9]+)}/{brightness:(-|[0-9]+)}', name = "hsb")
async def view_status_list(request):
    return JsonResponse(await switch(**validate(**request.match_info)))

@url('/switch/{number:[a-zA-Z-0-9]+}/off', name = "off")
async def view_status_list(request):
    return JsonResponse(await switch(**request.match_info, on = False))

@url('/websocket', name = "websocket")
async def websocket(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def ws_send(event):
        if not ws.closed:
            return await ws.send_str(dumps(event))
        print('attempt to write on closed ws')
        run_all(map(methodcaller('adispose'), tasks))

    tasks = await switches.subscribe(ws_send)

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == '/close':
                    await ws.close()
                else:
                    await app._handle(make_mocked_request('WS', msg.data))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %ws.exception())
    except asyncio.CancelledError:

        run_all(
            ws.close(),
            map(methodcaller('adispose'), tasks),
        )

    return ws

@url('/{all:.*}', name = 'not_found')
async def view_status_list(request):
    return JsonResponse(api_response(status = 404, message = 'PageNotFound'), status = 404)