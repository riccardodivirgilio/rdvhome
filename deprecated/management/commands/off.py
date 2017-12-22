# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from rdvhome.management.mqtt import MqttCommand
from rdvhome.toggles import all_toggles

class Command(MqttCommand, BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        all_toggles.switch(status = False)
        self.mqtt.publish(settings.MQTT_CHANNEL_COMMAND, reverse('status'))