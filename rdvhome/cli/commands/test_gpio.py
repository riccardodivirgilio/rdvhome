# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.conf import settings
from rdvhome.utils.async import syncronous_wait_all, wait_all
from rdvhome.utils.functional import iterate
from rdvhome.utils.gpio import get_gpio

import asyncio
import random

RELAY1 = settings.RASPBERRY_RELAY1
RELAY2 = settings.RASPBERRY_RELAY2
INPUT  = settings.RASPBERRY_INPUT

def shuffle(iterable):
    l = list(iterate(iterable))
    random.shuffle(l)
    return l

async def relay(number = [RELAY1[0], RELAY2[0]], timing = 0.1):

    gpio = get_gpio()

    for n in shuffle(number):
        await gpio.setup_output(n)

    #TURNING ON

    for n in shuffle(number):
        print("RELAY %.2i on" % n)
        await gpio.output(n, high = False)
        await asyncio.sleep(timing)

    for n in shuffle(number):
        print("RELAY %.2i off" % n)
        await gpio.output(n, high = True)
        await asyncio.sleep(timing)

async def read(number = INPUT, timing = 0.5, index = 1000):

    gpio = get_gpio()

    await wait_all(map(gpio.setup_input, iterate(number)))

    print(*(str(n).zfill(2) for n in iterate(number)))

    for i in range(index):

        results = await wait_all(map(gpio.input, iterate(number)))

        print(*((not v and str(n).zfill(2) or '--') for v, n in zip(results, iterate(number))))
        await asyncio.sleep(timing)

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):

        syncronous_wait_all(relay(**opts))
        syncronous_wait_all(read(**opts))