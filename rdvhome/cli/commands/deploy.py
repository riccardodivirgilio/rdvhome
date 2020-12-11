# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rpy.cli.utils import SimpleCommand
from rpy.functions.asyncio import syncronous_wait_all
from rpy.functions.importutils import module_path
from rdvhome.api import switch
from rdvhome.conf import settings
import os
import tempfile

SERVICE_TEMPLATE = """
[Unit]
Description=My service
After=network.target

[Service]
ExecStart=%(command)s
WorkingDirectory=%(directory)s
StandardOutput=inherit
StandardError=inherit
Restart=always
User=%(username)s

[Install]
WantedBy=multi-user.target
"""

def service(command, directory):
    return SERVICE_TEMPLATE % {'command': command, 'directory': directory, **server}

server = {
    'username': 'pi',
    'host': 'rdvhome.local',
    'home': "/home/pi/",
    'project': '/home/pi/rdvhome/'
}

class Command(SimpleCommand):

    def commands(self, **context):

        yield 'rsync -a %(local)s %(username)s@%(host)s:%(remote)s --exclude=node_modules/* --exclude=.git/* --size-only --delete -e "ssh -o StrictHostKeyChecking=no"' % context

        for cmd in self.local_commands(**context):
            yield ('ssh %(username)s@%(host)s -o StrictHostKeyChecking=no ' + cmd) % context

    def local_commands(self,  **context):
        yield 'python3 -m pip install %s --user' % " ".join(
            v and '%s==%s' % (n, v) or n
            for n, v in settings.DEPENDENCIES.items()

        )

        #yield "sudo systemctl restart lights.service"



    def handle(self, *args): 

     

        context = {
            'local': os.path.normpath(module_path('rdvhome', os.path.pardir)) + '/',
            'remote': "/home/pi/rdvhome/",
            **server
        }


        for cmd in tuple(self.commands(**context)):
            print(cmd)       
            os.system(cmd)