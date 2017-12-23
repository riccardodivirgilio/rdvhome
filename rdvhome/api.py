# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches import switches
from rdvhome.utils.datastructures import data

def api_response(status = 200, **kw):
    return data(
        kw,
        status  = status,
        success = status == 200,
    )

async def status_list():
    return api_response(
        mode     = "status",
        switches = await switches.status()
    )

async def status_detail(number):
    objs = switches.filter(number)
    return api_response(
        mode     = "status",
        switches = await objs.status(),
        status   = objs and 200 or 404
    )

async def switch(number, mode = None):
    objs = switches.filter(number)
    return api_response(
        mode     = "status",
        switches = await objs.switch(mode = mode),
        status   = objs and 200 or 404
    )