# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)

print "LED on"
GPIO.output(18,GPIO.HIGH)
time.sleep(0.3)

print "LED off"
GPIO.output(18,GPIO.LOW)