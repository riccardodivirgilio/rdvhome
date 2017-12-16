# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import RPi.GPIO as GPIO
import time

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from rdvhome.management.mqtt import MqttCommand

class Command(MqttCommand, BaseCommand):

    def handle(self, **options):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(18,GPIO.OUT)

        print "LED on"
        GPIO.output(18,GPIO.HIGH)
        time.sleep(0.3)

        print "LED off"
        GPIO.output(18,GPIO.LOW)