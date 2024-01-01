# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import logging
import sys
from operator import methodcaller

import aiohttp
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.web_exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound
from aiohttp.web_fileresponse import FileResponse
from rpy.functions.asyncio import run_all
from rpy.functions.decorators import to_data
from rpy.functions.importutils import module_path

from rdvhome.api import api_response, status, switch
from rdvhome.conf import settings
from rdvhome.switches import switches
from rdvhome.utils.colors import HSB, to_color
from rdvhome.utils.json import dumps


@web.middleware
async def server_error(request, handler):
    try:
        return await handler(request)

    except HTTPBadRequest as e:
        return JsonResponse(api_response(status=400, reason=str(e)))

    except HTTPForbidden as e:
        return JsonResponse(api_response(status=403, reason=str(e)))

    except HTTPNotFound as e:
        return JsonResponse(api_response(status=404, reason=str(e)))

    except Exception as e:

        logging.error(e, exc_info=True)

        if settings.DEBUG and not request.method == "WS":

            from django.conf import global_settings, settings as django_settings

            if not django_settings.configured:
                django_settings.configure(global_settings)
                django_settings.USE_I18N = False
                django_settings.SECRET_KEY = "hello"

            from django.views.debug import ExceptionReporter

            reporter = ExceptionReporter(None, *sys.exc_info(), is_email=False)

            return web.Response(
                text=reporter.get_traceback_html(), content_type="text/html", status=500
            )

        return JsonResponse(api_response(status=500))


app = web.Application(middlewares=[server_error])


def url(path, name, **opts):
    def inner(func):
        app.router.add_route("GET", path, func, name=name, **opts)
        app.router.add_route("WS", path, func, name="%s_ws" % name, **opts)

    return inner


def JsonResponse(data, status=None, **opts):
    return web.Response(text=dumps(data), status=status or data.status or 200, **opts)


def validate_color(spec):
    if spec in (None, "-"):
        return None
    try:
        spec = int(spec)
    except ValueError:
        raise HTTPBadRequest(reason="NotAnInteger")

    if spec > 100 or spec < 0:
        raise HTTPBadRequest(reason="NotInRange")
    else:
        return spec / 100


def getargs(request):
    return validate(**dict(request.query, **request.match_info))


@to_data
def validate(
    number=None,
    color=None,
    hue=None,
    saturation=None,
    brightness=None,
    mode=None,
    **extra,
):
    if number:
        yield "number", number

    if color:
        try:
            yield "color", to_color(color)
        except ValueError:
            raise HTTPBadRequest(reason="InvalidColor")

    args = tuple(map(validate_color, (hue, saturation, brightness)))

    if any(arg is not None for arg in args):
        yield "color", HSB(*args)

    if mode == "on":
        yield "on", True
    elif mode == "off":
        yield "on", False
    elif mode == "stop":
        yield "direction", None
    elif mode == "up":
        yield "direction", "up"
    elif mode == "down":
        yield "direction", "down"

    elif not mode in ("-", None):
        raise HTTPBadRequest(reason="InvalidMode")

@url("/", name="home")
async def view_home(request):
    return FileResponse(module_path("rdvhome", "frontend", "dist", "index.html"))

app.router.add_static("/css", module_path("rdvhome", "frontend", "dist", "css"))
app.router.add_static("/js", module_path("rdvhome", "frontend", "dist", "js"))


@url("/homekit", name="homekit")
async def homekit_pair(request):
    from rdvhome.homekit import driver

    return JsonResponse(
        api_response(
            paircode=driver.state.pincode.decode(), uri=driver.accessory.xhm_uri()
        )
    )


@url("/qrcode", name="homekit-qrcode")
async def homekit_pair(request):

    from rdvhome.homekit import driver
    from pyqrcode import QRCode
    import io

    stream = io.BytesIO()
    QRCode(driver.accessory.xhm_uri()).svg(stream, scale=14)
    stream.seek(0)

    return web.Response(body=stream.read(), status=200, content_type="image/svg+xml")


@url("/switch", name="status-list")
async def view_status_list(request):
    return JsonResponse(await status(**getargs(request)))


@url("/switch/{number:[a-zA-Z-0-9_-]+}", name="status")
async def view_status_list(request):
    return JsonResponse(await status(**getargs(request)))


@url("/switch/{number:[a-zA-Z-0-9_-]+}/set", name="switch")
async def view_status_list(request):
    return JsonResponse(await switch(**getargs(request)))


@url("/switch/{number:[a-zA-Z-0-9_-]+}/color/{color:[a-zA-Z-0-9]+}", name="color")
async def view_status_list(request):
    return JsonResponse(await switch(**getargs(request)))


@url("/switch/{number:[a-zA-Z-0-9_-]+}/{mode:(-|on|off|up|down|stop)}", name="on")
async def view_status_list(request):
    return JsonResponse(await switch(**getargs(request)))


@url(
    "/switch/{number:[a-zA-Z-0-9_-]+}/{mode:(-|on|off|up|down|stop)}/{hue:(-|[0-9]+)}/{saturation:(-|[0-9]+)}/{brightness:(-|[0-9]+)}",
    name="hsb",
)
async def view_status_list(request):
    return JsonResponse(await switch(**getargs(request)))


@url("/websocket", name="websocket")
async def websocket(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def ws_send(event):
        if not ws.closed:
            return await ws.send_str(dumps(event))
        print("attempt to write on closed ws")
        run_all(map(methodcaller("adispose"), tasks))

    tasks = await switches.subscribe(ws_send)

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == "/close":
                    await ws.close()
                else:
                    await app._handle(make_mocked_request("WS", msg.data))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("ws connection closed with exception %s" % ws.exception())
    except asyncio.CancelledError:

        run_all(ws.close(), map(methodcaller("adispose"), tasks))

    return ws
