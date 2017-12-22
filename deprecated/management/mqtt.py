# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.utils.functional import cached_property

from rdvhome.mqtt import Client as Mqtt

class MqttCommand(object):

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        pass

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        pass

    @cached_property
    def mqtt(self, *args, **options):
        return Mqtt(self.on_connect, self.on_message)