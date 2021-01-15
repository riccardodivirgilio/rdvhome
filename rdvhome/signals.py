# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.functions.datastructures import data

from rdvhome.state import switches, controllers
from rpy.functions.asyncio import run_all, wait_all


async def dispatch_status(number=None):
    target = switches.filter(number)
    return await wait_all(obj.status() for obj in target)

def generate_commands(target, **opts):
    for command, value in opts.items():
        for control in controllers:
            values = control.filter_switches_for(target, command)
            if values:
                yield control.switch(
                    values,
                    command,
                    value
                )

async def dispatch_switch(number=None, **opts):
    target = switches.filter(number)
    await wait_all(generate_commands(target, **opts))
    return target
