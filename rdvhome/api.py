# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.functions.datastructures import data

from rdvhome.state import switches


def api_response(status=200, **opts):
    return data(opts, status=status, success=status == 200)


async def status(number=None):
    objs = switches.filter(number)
    return api_response(
        mode="status", switches=await objs.status(), status=objs and 200 or 404
    )


async def switch(number=None, **opts):
    objs = switches.filter(number)
    return api_response(
        mode="status", switches=await objs.switch(**opts), status=objs and 200 or 404
    )
