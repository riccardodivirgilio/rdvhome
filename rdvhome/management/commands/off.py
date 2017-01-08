# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from rdvhome.management.mqtt import MqttCommand

class Command(MqttCommand, BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        self.mqtt.publish('command', reverse('toggle', kwargs = {'mode': False, 'number': "-".join(args or ['all'])}))