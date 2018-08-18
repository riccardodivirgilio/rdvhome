# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from fabric.api import env, execute, local, roles, run, sudo, task
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.main import main

from fabtools import require
from fabtools.supervisor import restart_process

from operator import attrgetter

import os
import sys

class Device(object):

    def __init__(self, id, ipaddress, name = None, user = None, default_password = "raspberry"):
        self.ipaddress = ipaddress
        self.name = name
        self.default_password = default_password
        self.user = user
        self.id = id

    def host(self):
        return "%s@%s:22" % (self.user, self.name or self.ipaddress)

RASPBERRY = Device(
    id = 'rasp',
    name = 'rdvpi.local',
    user = "pi",
    ipaddress = "192.168.1.193",
    default_password = "!w9Ij56LaoRKnP5fpV0LGH2GEHkY="
    )

NAS = Device(
    id = 'nas',
    name = 'rdvnas.local',
    user = "server",
    ipaddress = "192.168.1.200",
    #default_password = "!w9Ij56LaoRKnP5fpV0LGH2GEHkY="
    )

#env.passwords = {'pi@rdvpi.local:22': 'raspberry'}
env.roledefs  = {
    'lights': [RASPBERRY.host()],
    'nas':    [NAS.host()],
}

env.passwords = {
    RASPBERRY.host(): RASPBERRY.default_password
}

@task
@roles('lights')
def setup():

    require.user(
        env.user,
        password = '!w9Ij56LaoRKnP5fpV0LGH2GEHkY=',
        ssh_public_keys = [os.path.expanduser("~/.ssh/id_rsa.pub")]
    )

    require.deb.uptodate_index()
    require.deb.packages([
       'ntpdate',
       'rsync',
       'python3',
       'python3-dev',
       'python3-rpi.gpio',
       'avahi-daemon',
       'avahi-discover',
       'libnss-mdns',
    ])

    #sudo("ntpdate -s time.nist.gov")
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
@roles('lights')
def supervisor():
    require.supervisor.process(
        'server',
        command='python3.6 /home/pi/server/run.py run',
        directory='/home/pi/server/',
        user=env.user
    )

@task
@roles('lights')
def run_command(cmd = 'test_gpio'):
    execute(deploy, restart = False)
    run('python3.6 /home/pi/server/run.py %s' % cmd)

@task
@roles('lights')
def deploy(restart = True, branch = 'master'):

    require.git.working_copy(
        remote_url = 'git@bitbucket.org:riccardodivirgilio/rdvhome.git',
        path = '/home/pi/server/',
        branch = branch
    )

    if restart:
        restart_process("server")

@task
@roles('home')
def shutdown():
    sudo("shutdown now")

#START NAS

@task
@roles('nas')
def setup_nas():

    require.deb.uptodate_index()
    require.deb.packages([
        'ntpdate',
        'rsync',
        'python2',
        'python2-dev',
        'python3',
        'python3-dev',
        'avahi-daemon',
        'avahi-discover',
        'libnss-mdns'
    ])

    sudo("ntpdate -s time.nist.gov")
    sudo("timedatectl set-timezone Europe/Rome")
    require.system.default_locale("en_US.UTF-8")

    require.user(
        env.user,
        password = env.password,
        ssh_public_keys = [os.path.expanduser("~/.ssh/id_rsa.pub")]
    )

    require.python.pip(python_cmd="python")
    require.python.pip(python_cmd="python3")

@task
@roles('nas')
def shutdown_nas():
    sudo("shutdown now")

@task
@roles('nas')
def backup(master = True, slave = True, verbose = False):

    for local, remote, extra in (
        ("~/Pictures/",    "raw/",     ''),
        ("~/Photos/",      "photos/",  ''),
        #("~/Git/",         "git/",     '--delete'),
        #("~/Wolfram/git/", "wolfram/", '--delete'),
        #("~/Private/",     "private/", '--delete'),
        #("~/Desktop/",     "desktop/", '--delete'),
        ):

        if verbose:
            extra += ' -v --progress'

        if master:
            rsync_project(
                local_dir  = os.path.expanduser(local),
                remote_dir = "/home/server/master/%s" % remote,
                extra_opts = ' %s --size-only' % extra
            )
        if slave:
            run('rsync -pthrvz %s --size-only /home/server/master/%s /home/server/slave/%s' % (extra, remote, remote))

@task
@roles('nas')
def backup_master():
    execute(backup, master = True, slave = False)

@task
@roles('nas')
def backup_slave():
    execute(backup, master = False, slave = True)

@task
@roles('nas')
def move_pictures(to_keep = 1000):

    LOCAL  = os.path.expanduser('~/Pictures/')
    REMOTE = '/Volumes/Master/raw'

    if not os.path.exists(REMOTE):
        local('open afp://%s:server@%s/Master' % (
            NAS.user,
            NAS.name,
        ))

    files = sorted(
        filter(
            lambda f: not f.is_symlink() and os.path.splitext(f)[1].lower() == '.nef',
            os.scandir(LOCAL)
        ),
        key = lambda f: f.stat().st_ctime
    )

    if len(files) > to_keep:

        symlinks = frozenset(map(attrgetter('name'), files[:-to_keep])).intersection(os.listdir(REMOTE))

        for name in symlinks:

            local  = os.path.join(LOCAL, name)
            remote = os.path.join(REMOTE, name)

            os.remove(local)
            os.symlink(remote, local)

            print(local, '>>', remote)

if __name__ == '__main__':
    sys.argv = ['fab', '-f', __file__] + sys.argv[1:]
    main()