# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from operator import attrgetter
from rpy.functions.importutils import module_path
from fabric.api import env, execute, local, roles, run, sudo, task
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.main import main
from fabtools import require

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
User=pi

[Install]
WantedBy=multi-user.target
"""

def service(command, directory):
    return SERVICE_TEMPLATE % {'command': command, 'directory': directory}


class Device(object):
    def __init__(
        self, id, name=None, user=None, default_password="raspberry"
    ):
        self.name = name
        self.default_password = default_password
        self.user = user
        self.id = id

    def host(self):
        return "%s@%s:22" % (self.user, self.name)


RASPBERRY = Device(
    id="rasp",
    name="rdvpi.local",
    user="pi",
    default_password="death4normals!"
)

DOORBELL = Device(
    id="doorbell",
    name="rdvdoorbell.local",
    user="pi",
    default_password="death4normals!"
)

# env.passwords = {'pi@rdvpi.local:22': 'raspberry'}
env.roledefs = {
    "lights": [RASPBERRY.host()], 
    "doorbell": [DOORBELL.host()],
    "devices": [DOORBELL.host(), RASPBERRY.host()],
    }

env.passwords = {
    RASPBERRY.host(): RASPBERRY.default_password,
    DOORBELL.host(): DOORBELL.default_password,
}


@task
@roles("doorbell")
def setup():

    sudo('apt-get update')
    sudo('apt-get install ntpdate rsync python3 python3-rpi.gpio avahi-daemon avahi-discover libnss-mdns -y')
    sudo("timedatectl set-timezone Europe/Rome")    

    if not exists("/swapfile"):
        sudo("fallocate -l 4G /swapfile")
        sudo("chmod 600 /swapfile")
        sudo("mkswap /swapfile")
        sudo("swapon /swapfile")
    if not "/swapfile" in sudo("cat /etc/fstab"):
        sudo('echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab')

@task
@roles("lights")
def deploy(restart=True):

    require.file(
        '/etc/systemd/system/lights.service', 
        contents=service('python3 /home/pi/rdvhome/run.py run', '/home/pi/rdvhome/'), 
        use_sudo=True,
        mode = '700'
    )

    rsync_project(
        local_dir=os.path.normpath(module_path('rdvhome', os.path.pardir)),
        remote_dir="/home/pi/",
        extra_opts=" --exclude=node_modules/* --exclude=.git/* --size-only --delete",
    )

    if restart:
        sudo("sudo systemctl restart lights.service")
        #sudo("sudo systemctl start lights.service")


if __name__ == "__main__":
    sys.argv = ["fab", "-f", __file__] + sys.argv[1:]
    main()
