from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.conf import settings
from rdvhome.utils.gpio import get_gpio

from rpy.cli.utils import SimpleCommand
from rpy.functions.asyncio import syncronous_wait_all, wait_all
from rpy.functions.functional import iterate

import asyncio

RELAY1 = settings.RASPBERRY_RELAY1
RELAY2 = settings.RASPBERRY_RELAY2
INPUT = settings.RASPBERRY_INPUT

async def relay(number=RELAY2, timing=0.2, timing_between=1):

    gpio = get_gpio()

    for n in iterate(number):
        await gpio.setup_output(n)

    # TURNING ON

    for n in iterate(number):
        print("RELAY %.2i on" % n)
        await gpio.output(n, high=False)
        await asyncio.sleep(timing)

    await asyncio.sleep(timing_between)

    for n in iterate(number):
        print("RELAY %.2i off" % n)
        await gpio.output(n, high=True)
        await asyncio.sleep(timing)

async def read(number=INPUT, timing=0.5, index=1000):

    gpio = get_gpio()

    await wait_all(map(gpio.setup_input, iterate(number)))

    print(*(str(n).zfill(2) for n in iterate(number)))

    for i in range(index):

        results = await wait_all(map(gpio.input, iterate(number)))

        print(*((not v and str(n).zfill(2) or "--") for v, n in zip(results, iterate(number))))
        await asyncio.sleep(timing)

async def callback(number=INPUT):

    gpio = get_gpio()

    async def echo(e):
        print(e)

    await wait_all(
        (gpio.setup_input(n, callback=echo, bouncetime=200) for n in iterate(number))
    )

    print(*(str(n).zfill(2) for n in iterate(number)))

    while True:
        await asyncio.sleep(0.1)

class Command(SimpleCommand):

    help = "Test GPIO"

    def handle(self, **opts):

        syncronous_wait_all(relay(**opts))
        # syncronous_wait_all(read(**opts))
        # syncronous_wait_all(callback(**opts))