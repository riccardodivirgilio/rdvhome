# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from aiohttp import web

from functools import partial

from rdvhome.api import api_response, status_detail, status_list, switch
from rdvhome.utils.json import dumps

app = web.Application()

def url(path, **opts):
    def inner(func):
        return app.router.add_get(path, func, **opts)
    return inner

def JsonResponse(data, **opts):
    return web.Response(text = dumps(data), **opts)

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