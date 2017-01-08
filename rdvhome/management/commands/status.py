# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.management.mqtt import MqttCommand

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

class Command(MqttCommand, BaseCommand):

    def handle(self, **options):
        self.mqtt.publish('command', reverse('status'))