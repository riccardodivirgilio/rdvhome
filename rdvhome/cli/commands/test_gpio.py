# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.utils.functional import iterate

import time

RELAY1 = [22, 27, 17,  4,  3,  2]

RELAY2 = [16, 12,  7,  8, 25, 24]

INPUT  = [21, 20, 23, 18, 26, 19, 
          13,  6,  5, 10,  9, 11]

def relay(number = list(iterate(RELAY1, RELAY2)), timing = 0.1):

    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for n in iterate(number):
        GPIO.setup(n, GPIO.OUT)

    for n in iterate(number):
        GPIO.output(n, GPIO.HIGH)

    #TURNING ON

    for n in iterate(number):
        print("RELAY %s on" % n)
        GPIO.output(n, GPIO.LOW)
        time.sleep(timing)

    for n in iterate(number):
        print("RELAY %s off" % n)
        GPIO.output(n, GPIO.HIGH)
        time.sleep(timing)

def read(number = INPUT):
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for n in iterate(number):
        GPIO.setup(n, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    print(*(str(n).zfill(2) for n in iterate(number)))

    for i in range(10):
        print(*(str(not GPIO.input(n) and n or '-').rjust(2) for n in iterate(number)))
            
        time.sleep(0.5)

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):
        #relay(**opts)
        read(**opts)