# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

#need to use this
#http://hbmqtt.readthedocs.io/en/latest/references/broker.html

from django.conf import settings

def Client(on_connect = None, on_message = None):
    from paho.mqtt.client import Client as Mqtt
    mqtt = Mqtt()
    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    if settings.MQTT_BROKER_USERNAME:
        mqtt.username_pw_set(settings.MQTT_BROKER_USERNAME, settings.MQTT_BROKER_PASSWORD)
    mqtt.connect(settings.MQTT_BROKER_URL, settings.MQTT_BROKER_PORT, 60)
    #mqtt.connect("localhost", 1883, 60)
    return mqtt