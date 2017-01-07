# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.handlers.base import logger
from django.core.management.commands.runserver import Command as RunServer
from django.test import Client
from django.utils.encoding import force_str

from paho.mqtt.client import Client as Mqtt

import sys

class Command(RunServer):

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.stdout.write("Connected to channel command")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("command")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        self.stdout.write("%s: %s" % (msg.topic, force_str(msg.payload)))
        try:
            response = self.client.get(msg.payload)
            if response.status_code == 200:
                self.mqtt.publish("status", response.content)
        except Exception as e:
            logger.error(
                "Error %s" % e,
                exc_info=sys.exc_info(),
                extra={'status_code': 500}
            )

    def inner_run(self, *args, **options):
        self.client = Client()
        self.mqtt = Mqtt()
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message
        self.mqtt.connect("localhost", 1883, 60)
        self.mqtt.loop_forever()