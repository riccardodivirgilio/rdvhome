# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.handlers.base import logger
from django.core.management.commands.runserver import Command as RunServer
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils.encoding import force_str

from rdvhome.management.mqtt import MqttCommand

import sys

class Command(MqttCommand, RunServer):

    def handle_payload(self, payload):
        self.stdout.write(force_str(payload))
        try:
            response = self.client.get(payload)
            if response.status_code == 200:
                self.mqtt.publish("status", response.content)
        except Exception as e:
            logger.error(
                "Error %s" % e,
                exc_info=sys.exc_info(),
                extra={'status_code': 500}
            )        

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.stdout.write("Connected to channel command")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("command")
        self.handle_payload(reverse('status'))

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        self.handle_payload(msg.payload)

    def inner_run(self, *args, **options):
        self.client = Client()
        self.mqtt.loop_forever()