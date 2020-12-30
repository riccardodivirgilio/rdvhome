# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os

from rpy.cli.utils import SimpleCommand
from rpy.functions.importutils import module_path
from rdvhome.switches import switches
from rdvhome.conf import settings
from itertools import groupby
import base64
SERVICE_TEMPLATE = """
[Unit]
Description=Light 1
After=network.target

[Service]
ExecStart=%(command)s
WorkingDirectory=%(project)s
StandardOutput=inherit
StandardError=inherit
Restart=always
User=%(username)s

[Install]
WantedBy=multi-user.target
"""

def service(command, **context):
    return SERVICE_TEMPLATE % {'command': command, **context}

def b64encode(content):
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')

server = {
    'username': 'pi',
    'host': 'rdvhome.local',
    'home': "/home/pi/",
    'project': '/home/pi/rdvhome/',
    'local': os.path.normpath(module_path('rdvhome', os.path.pardir)) + '/',
}

class Command(SimpleCommand):

    def commands(self, **context):

        yield 'rsync -a %(local)s %(username)s@%(host)s:%(project)s --exclude=node_modules/* --exclude=.git/* --size-only --delete' % context

        for cmd in self.local_commands(**context):
            yield ('ssh %(username)s@%(host)s ' + cmd) % context

    def local_files(self, **context):
        yield '/etc/systemd/system/gpioserver.service', service('python3 -m gpioserver --output-high=5,6,9,11,13,14,15,16,18,20,21,23,24,27 --input-pull-up=2,3,4,7,8,12,17,25', **context)
        yield '/etc/systemd/system/lights.service', service('python3 /home/pi/rdvhome/run.py run', **context)

    def local_commands(self,  **context):

        for path, content in self.local_files(**context):
            yield "'echo %s | base64 --decode > /tmp/tempfile'" % b64encode(content)
            yield 'sudo cp /tmp/tempfile %s' % path

        yield 'python3 -m pip install %s --user' % " ".join(
            v and '%s==%s' % (n, v) or n
            for n, v in settings.DEPENDENCIES.items()

        )
        yield "sudo systemctl daemon-reload"
        yield "sudo systemctl stop lights.service"
        yield "sudo systemctl start gpioserver.service"

    def handle(self, *args): 
        for cmd in tuple(self.commands(**server)):
            print(cmd)       
            os.system(cmd)
