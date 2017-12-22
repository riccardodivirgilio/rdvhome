# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, Template

import os

CONTANTS = Template("""

// Constant utility class
package com.rdv.client;

public class Settings {
    private Settings() { }  // Prevents instantiation

    public static final String MQTT_CHANNEL_COMMAND = "{{ settings.MQTT_CHANNEL_COMMAND }}";
    public static final String MQTT_CHANNEL_STATUS  = "{{ settings.MQTT_CHANNEL_STATUS }}";
    public static final String MQTT_BROKER_URL = "tcp://{{ settings.MQTT_BROKER_URL }}:{{ settings.MQTT_BROKER_PORT|safe }}";
    public static final String MQTT_BROKER_PASSWORD = "{{ settings.MQTT_BROKER_PASSWORD|default:'' }}";
    public static final String MQTT_BROKER_USERNAME = "{{ settings.MQTT_BROKER_USERNAME|default:'' }}";
    public static final String MQTT_INITIAL_COMMAND = "{% url 'status' %}";

}

""")

class Command(BaseCommand):

    def handle(self, **options):

        import rdvhome

        devices = os.path.join(
            os.path.dirname(rdvhome.__file__),
            os.pardir,
            "client/app/src/main/java/com/rdv/client/Settings.java"
        )
        with open(devices, "w") as f:
            f.write(CONTANTS.render(Context({"settings": settings})))