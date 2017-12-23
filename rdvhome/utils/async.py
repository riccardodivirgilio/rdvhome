# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from operator import methodcaller

from rdvhome.utils.functional import iterate

import asyncio

async def wait_all(*args):
    done, _ = await asyncio.wait(tuple(iterate(*args)))
    return map(methodcaller('result'), done)

def syncronous_wait_all(*args):
    yield from asyncio.get_event_loop().run_until_complete(wait_all(*args))