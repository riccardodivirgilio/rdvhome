# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from rdvhome.management.mqtt import MqttCommand
from django.conf import settings

class Command(MqttCommand, BaseCommand):

    def handle(self, **options):
        self.mqtt.publish(settings.MQTT_CHANNEL_COMMAND, reverse('status'))