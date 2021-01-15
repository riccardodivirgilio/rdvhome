# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.functions.datastructures import data

from rdvhome.state import switches, controllers
from rpy.functions.asyncio import run_all, wait_all

def api_response(status=200, **opts):
    return data(opts, status=status, success=status == 200)


async def status(number=None):
    target = switches.filter(number)

    return api_response(
        mode="status", 
        status=target and 200 or 404,
        switches={
            serialized.id: serialized
            for serialized in await wait_all(obj.status() for obj in target)
        }
    )


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

async def switch(number=None, **opts):
    target = switches.filter(number)

    await wait_all(generate_commands(target, **opts))

    return api_response(
        mode="switch", 
        status=target and 200 or 404,
        switches=[obj.id for obj in target], 
        **opts
    )
