# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.switches import switches
from rdvhome.utils.datastructures import data

def status_verbose(mode = None):
    return mode and "on" or "off"

def api_response(status = 200, **kw):
    return data(
        kw,
        status = status,
        success = status == 200,
    )

def status_list():
    return api_response(mode = "status", switches = switches)

def status_detail(number):
    switches = switches.filter(number)
    return api_response(
        mode = "status",
        switches = switches,
        status = switches and 200 or 404
    )

def switch(number, mode = None):
    switches = switches.filter(number)
    switches.switch(mode)
    return api_response(
        mode = "status",
        switches = switches,
        status = switches and 200 or 404
    )