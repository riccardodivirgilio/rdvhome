

from rdvhome.state import controllers, switches

from rpy.functions.asyncio import wait_all
import asyncio


async def dispatch_status(number=None):
    target = switches.filter(number)

    for obj in target:
        asyncio.create_task(obj.status())

    return target

async def dispatch_switch(number=None, **opts):
    target = switches.filter(number)

    for command, value in opts.items():
        for control in controllers:
            values = control.filter_switches_for(target, command)
            if values:
                asyncio.create_task(control.switch(values, command, value))

    return target