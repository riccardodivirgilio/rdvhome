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
from fabtools.supervisor import restart_process


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
)

DOORBELL = Device(
    id="doorbell",
    name="rdvdoorbell.local",
    user="pi",
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

    #require.user(
    #    env.user,
    #    password="!w9Ij56LaoRKnP5fpV0LGH2GEHkY=",
    #    ssh_public_keys=[os.path.expanduser("~/.ssh/id_rsa.pub")],
    #)

    require.deb.uptodate_index()
    require.deb.packages(
        [
            "ntpdate",
            "rsync",
            "python3",
            "python3-dev",
            "python3-rpi.gpio",
            "avahi-daemon",
            "avahi-discover",
            "libnss-mdns",
        ]
    )

    # sudo("ntpdate -s time.nist.gov")
    sudo("timedatectl set-timezone Europe/Rome")
    require.system.default_locale("en_US.UTF-8")

    if not exists("/swapfile"):
        sudo("fallocate -l 4G /swapfile")
        sudo("chmod 600 /swapfile")
        sudo("mkswap /swapfile")
        sudo("swapon /swapfile")
    if not "/swapfile" in sudo("cat /etc/fstab"):
        sudo('echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab')

    require.python.pip(python_cmd="python")
    require.python.pip(python_cmd="python3")


@task
@roles("lights")
def supervisor():
    require.supervisor.process(
        "server",
        command="python3.6 /home/pi/rdvhome/run.py run",
        directory="/home/pi/rdvhome/",
        user=env.user,
    )


@task
@roles("lights")
def run_command(cmd="test_gpio"):
    execute(deploy, restart=False)
    run("python3.6 /home/pi/rdvhome/run.py %s" % cmd)


@task
@roles("lights")
def deploy(restart=True, branch="master"):

    rsync_project(
        local_dir=os.path.normpath(module_path('rdvhome', os.path.pardir)),
        remote_dir="/home/pi/",
        extra_opts=" --exclude=node_modules/* --size-only",
    )

    if restart:
        restart_process("server")


if __name__ == "__main__":
    sys.argv = ["fab", "-f", __file__] + sys.argv[1:]
    main()
