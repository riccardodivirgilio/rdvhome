# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.template import Context, Template

from rdvhome.constants import RASPBERRY

import os

XML = Template("""
<resources>
    <!-- Strings related to devices -->
    <string name="device/ip">{{ raspberry.ipaddress }}</string>
    <string name="device/name">{{ raspberry.name }}</string>{% for id, data in raspberry.gpio.items %}
    <string name="gpio/{{ id }}">{{ data.label|default:id }}</string>{% endfor %}
</resources>
""")

class Command(BaseCommand):

    def handle(self, **options):

        import rdvhome

        devices = os.path.join(
            os.path.dirname(rdvhome.__file__),
            os.pardir,
            os.pardir,
            "rdvauth/app/src/main/res/values/devices.xml"
        )

        with open(devices, "w") as f:
            f.write(XML.render(Context({"raspberry": RASPBERRY})))