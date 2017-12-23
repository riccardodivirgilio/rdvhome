# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from functools import partial

from rdvhome.api import api_response, status, switch
from rdvhome.conf import settings
from rdvhome.utils.json import dumps
from rdvhome.utils.importutils import module_path

import logging
import sys
import traceback

@web.middleware
async def server_error(request, handler):
    try:
        return await handler(request)
    except Exception as e:

        logging.error(e, exc_info=True)

        if settings.DEBUG:

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

def url(path, **opts):
    def inner(func):
        return app.router.add_get(path, func, **opts)
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
    <title>%(title)s</title>
  </head>
  <body>
    <div id="app"></div>
    <script>%(js)s</script>
  </body>
</html>"""

@url('/')
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
    return JsonResponse(await status())

@url('/switch/{number:[a-zA-Z-0-9]+}', name = "status")
async def view_status_list(request):
    return JsonResponse(await status(request.match_info['number']))

@url('/switch/{number:[a-zA-Z-0-9]+}/on', name = "on")
async def view_status_list(request):
    return JsonResponse(await switch(request.match_info['number'], mode = True))

@url('/switch/{number:[a-zA-Z-0-9]+}/off', name = "off")
async def view_status_list(request):
    return JsonResponse(await switch(request.match_info['number'], mode = False))

@url('/{all:.*}')
async def view_status_list(request):
    return JsonResponse(api_response(status = 404, message = 'PageNotFound'), status = 404)