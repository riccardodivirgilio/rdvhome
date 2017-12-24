# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from operator import methodcaller

from rdvhome.utils.functional import iterate, first

import asyncio

async def wait_all(*args):
    done = tuple(iterate(*args))
    if done:
        done, _ = await asyncio.wait(done)
        return map(methodcaller('result'), done)

    return done

def run_all(*args):
    done = tuple(iterate(*args))
    if done and len(done) > 1:
        return asyncio.ensure_future(asyncio.wait(done))
    elif done:
        return asyncio.ensure_future(first(done))
    return done

def syncronous_wait_all(*args, loop = None):
    yield from (loop or asyncio.get_event_loop()).run_until_complete(wait_all(*args))