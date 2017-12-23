# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.utils.functional import iterate
from operator import methodcaller
import asyncio

async def wait_all(*args):
    done, _ = await asyncio.wait(tuple(iterate(*args)))
    return map(methodcaller('result'), done)