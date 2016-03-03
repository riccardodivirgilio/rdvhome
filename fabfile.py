# -*- coding: utf-8 -*-

from fabric.api import env, roles, run, sudo, task
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

from fabtools import require
from fabtools.supervisor import restart_process

import os

env.roledefs  = {'home': ['pi@rdvpi.local:22']}
#env.passwords = {'pi@rdvpi.local:22': 'raspberry'}

@task
@roles('home')
def setup():

    require.deb.uptodate_index()
    require.deb.packages([
       'ntpdate',
       'rsync',
       'python2',
       'python2-dev',
       'python3',
       'python3-dev',
    ])

    sudo("ntpdate -s time.nist.gov")
    sudo("timedatectl set-timezone Europe/Rome")
    require.system.default_locale("en_US.UTF-8")

    require.user(
        env.user,
        password = '!w9Ij56LaoRKnP5fpV0LGH2GEHkY=',
        ssh_public_keys = [os.path.expanduser("~/.ssh/id_rsa.pub")]
    )

    #if not exists("/swapfile"):
    #    sudo("fallocate -l 4G /swapfile")
    #    sudo("chmod 600 /swapfile")
    #    sudo("mkswap /swapfile")
    #    sudo("swapon /swapfile")
    #if not "/swapfile" in sudo("cat /etc/fstab"):
    #    sudo('echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab')

    require.python.pip(python_cmd="python")
    require.python.pip(python_cmd="python3")

    execute(dependency)
    execute(deploy, init_supervisor = True)

@task
@roles('home')
def dependency():
    run("pip3 install aiohttp aiohttp_wsgi RPi.GPIO django --user")

@task
@roles('home')
def deploy(init_supervisor = False):
    rsync_project(
        remote_dir="/home/pi/server/",
        local_dir="%s/" % os.path.dirname(__file__),
        exclude=("*.pyc", ".git/*"),
        delete=True
        )

    if init_supervisor:
        require.supervisor.process(
            'server',
            command='python3 /home/pi/server/server.py',
            directory='/home/pi/server/',
            user=env.user
            )
    else:
        restart_process("server")

@task
@roles('home')
def shutdown():
    sudo("shutdown now")