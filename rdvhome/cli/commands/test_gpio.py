# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.utils.functional import iterate
from rdvhome.utils.gpio import get_gpio

import time

RELAY1 = [22, 27, 17,  4,  3,  2]

RELAY2 = [16, 12,  7,  8, 25, 24]

INPUT  = [21, 20, 23, 18, 26, 19, 
          13,  6,  5, 10,  9, 11]

def relay(number = list(iterate(RELAY1, RELAY2)), timing = 0.1):

    gpio = get_gpio()

    for n in iterate(number):
        gpio.setup_output(n)

    #TURNING ON

    for n in iterate(number):
        print("RELAY %s on" % n)
        gpio.output(n, high = False)
        time.sleep(timing)

    for n in iterate(number):
        print("RELAY %s off" % n)
        gpio.output(n, high = True)
        time.sleep(timing)

def read(number = INPUT):

    gpio = get_gpio()

    for n in iterate(number):
        gpio.setup_input(n)

    print(*(str(n).zfill(2) for n in iterate(number)))

    for i in range(10):
        print(*(str(not gpio.input(n) and n or '-').rjust(2) for n in iterate(number)))
        time.sleep(0.5)

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):
        relay(**opts)
        read(**opts)