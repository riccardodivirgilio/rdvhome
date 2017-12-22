# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.encoding import JSONEncoder
from rdvhome.toggles import all_toggles
from rdvhome.utils.datastructures import data

def status_verbose(mode = None):
    return mode and "on" or "off"

def api_response(request = None, status_code = 200, **kw):
    return data(
        kw,
        code = status_code,
        success = status_code == 200,
    )

def status_list(request):
    return api_response(mode = "status", toggles = all_toggles)

def filter_toggles(number):
    return all_toggles.filter(number)

def status_detail(request, number):
    toggles = filter_toggles(number)
    return api_response(
        mode = "status",
        toggles = toggles,
        status_code = toggles and 200 or 404
    )

def output_switch(request, number, mode = None):
    toggles = filter_toggles(number)
    toggles.switch(mode)
    return api_response(
        mode = "status",
        toggles = toggles,
        status_code = toggles and 200 or 404
    )