# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.utils import SimpleCommand

import time

def test(number = 3):
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(number, GPIO.OUT)
    print("LED on")
    GPIO.output(number, GPIO.HIGH)
    time.sleep(1)
    print("LED off")
    GPIO.output(number, GPIO.LOW)

class Command(SimpleCommand):

    help = 'Test GPIO'

    def handle(self, **opts):
        test(**opts)