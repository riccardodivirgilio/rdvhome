# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.utils import six

import aiohttp
import asyncio

def do_request(session, url):
    if isinstance(url, six.string_types):
        return session.get(url)
    return url(session)

async def async_fetch(session, url, as_json = True):
    with aiohttp.Timeout(10):
        async with do_request(session, url) as response:
            if as_json:
                return await response.json()
            else:
                return await response.text()

async def async_fetch_all(session, urls, loop, **opts):
    return await asyncio.wait([
        loop.create_task(async_fetch(session, url, **opts))
        for url in urls
    ])

def fetch_all(urls, **opts):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with aiohttp.ClientSession(loop=loop) as session:
        done, _ = loop.run_until_complete(async_fetch_all(session, urls, loop, **opts))
        for future in done:
            yield future.result()