# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from fabric.api import env, roles, run, sudo, task
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.api import env, roles, run, sudo, task, execute
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.main import main
from fabtools import require
from fabtools.supervisor import restart_process

import os
import sys
from fabtools import require
from fabtools.supervisor import restart_process

from rdvhome.server import NAS, RASPBERRY

import os

#env.passwords = {'pi@rdvpi.local:22': 'raspberry'}
env.roledefs  = {
    'home': [RASPBERRY.host()], 
    'nas':  [NAS.host()]
}

env.passwords = {
    NAS.host(): 'server'
}


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
       'avahi-daemon',
       'avahi-discover',
       'libnss-mdns'
    ])

    sudo("ntpdate -s time.nist.gov")
    sudo("timedatectl set-timezone Europe/Rome")
    require.system.default_locale("en_US.UTF-8")

    require.user(
        env.user,
        password = '!w9Ij56LaoRKnP5fpV0LGH2GEHkY=',
        ssh_public_keys = [os.path.expanduser("~/.ssh/id_rsa.pub")]
    )

    if not exists("/swapfile"):
        sudo("fallocate -l 4G /swapfile")
        sudo("chmod 600 /swapfile")
        sudo("mkswap /swapfile")
        sudo("swapon /swapfile")
    if not "/swapfile" in sudo("cat /etc/fstab"):
        sudo('echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab')

    require.python.pip(python_cmd="python")
    require.python.pip(python_cmd="python3")

    execute(dependency)
    execute(supervisor)
    execute(deploy, restart = False)
    execute(nginx)

SITE_TEMPLATE = """\

upstream django {
    server localhost:45000;
}

server {
    listen      80;
    server_name   %(host)s;

    location / {
        # uncomment to switch to manteinance mode
        # return 503;
        # host and port to fastcgi server
        uwsgi_pass django;

        uwsgi_param  QUERY_STRING       $query_string;
        uwsgi_param  REQUEST_METHOD     $request_method;
        uwsgi_param  CONTENT_TYPE       $content_type;
        uwsgi_param  CONTENT_LENGTH     $content_length;
        uwsgi_param  REQUEST_URI        $request_uri;
        uwsgi_param  PATH_INFO          $document_uri;
        uwsgi_param  DOCUMENT_ROOT      $document_root;
        uwsgi_param  SERVER_PROTOCOL    $server_protocol;
        uwsgi_param  REQUEST_SCHEME     $scheme;
        uwsgi_param  HTTPS              $https if_not_empty;
        uwsgi_param  REMOTE_ADDR        $remote_addr;
        uwsgi_param  REMOTE_PORT        $remote_port;
        uwsgi_param  SERVER_PORT        $server_port;
        uwsgi_param  SERVER_NAME        $server_name;
    }
}
"""

@task
@roles('home')
def nginx():
    require.nginx.site(
        'server',
        template_contents = SITE_TEMPLATE,
        host = env.host,
        check_config = False
        )

@task
@roles('home')
def dependency():
    run("pip3 install uwsgi RPi.GPIO django --user")

@task
@roles('home')
def supervisor():
    require.supervisor.process(
        'server',
        command='/usr/local/bin/uwsgi --chdir=/home/pi/server/ --module=rdvhome.wsgi:application --master --pidfile=/home/pi/application.pid --socket=0.0.0.0:45000',
        directory='/home/pi/server/',
        user=env.user
        )

    #require.supervisor.process(
    #    'server',
    #    command='python3 /home/pi/server/server.py',
    #    directory='/home/pi/server/',
    #    user=env.user
    #    )

@task
@roles('home')
def deploy(restart = True):
    rsync_project(
        remote_dir="/home/pi/server/",
        local_dir="%s/" % os.path.dirname(__file__),
        exclude=("*.pyc", ".git/*"),
        delete=True
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
def backup(master = True, slave = True, verbose = True):

    for local, remote, extra in (
        ("~/Pictures/", "raw/",     ''),
        ("~/Photos/",   "photos/",  ''),
        ("~/Git/",      "git/",     '--delete'),
        ("~/Wolfram/",  "wolfram/", '--delete'),
        ("~/Private/",  "private/", '--delete'),
        ("~/Desktop/",  "desktop/", '--delete'),
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


if __name__ == '__main__':  
    sys.argv = ['fab', '-f', __file__] + sys.argv[1:]
    main()
