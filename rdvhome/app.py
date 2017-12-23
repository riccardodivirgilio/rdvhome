# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from functools import partial

from rdvhome.api import api_response, status_detail, status_list, switch
from rdvhome.conf import settings
from rdvhome.utils.json import dumps

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

@url('/')
async def view_home(request):
    return web.Response(text = 'hello!')

@url('/switch', name = "status-list")
async def view_status_list(request):
    return JsonResponse(status_list())

@url('/switch/{number:[a-zA-Z-0-9]+}', name = "status")
async def view_status_list(request):
    return JsonResponse(status_detail(request.match_info['number']))

@url('/switch/{number:[a-zA-Z-0-9]+}/on', name = "on")
async def view_status_list(request):
    return JsonResponse(switch(request.match_info['number'], mode = True))

@url('/switch/{number:[a-zA-Z-0-9]+}/off', name = "off")
async def view_status_list(request):
    return JsonResponse(switch(request.match_info['number'], mode = False))

@url('/{all:.*}')
async def view_status_list(request):
    return JsonResponse(api_response(status = 404, message = 'PageNotFound'), status = 404)