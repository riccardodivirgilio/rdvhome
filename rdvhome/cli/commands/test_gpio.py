# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand
from rdvhome.utils.functional import iterate

import time

LED1   = 18
LED2   = 23
RELAY1 = 16

def test(number = [RELAY1]):

    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for n in iterate(number):
        GPIO.setup(n, GPIO.OUT)
        print("LED %s on" % n)
        GPIO.output(n, GPIO.HIGH)

    time.sleep(2)

    for n in iterate(number):
        print("LED %s off" % n)
        GPIO.output(n, GPIO.LOW)

def read(number = [21]):

    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for n in iterate(number):
        GPIO.setup(n, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    for i in range(10):
        for n in iterate(number):
            print(GPIO.input(n))
            time.sleep(0.5)

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):
        #test(**opts)
        read(**opts)