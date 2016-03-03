from fabric.api import env, task, run, sudo, roles

env.roledefs  = {'home': ['pi@rdvpi.local:22']}
env.passwords = {'pi@rdvpi.local:22': 'raspberry'}

@roles('home')
def deploy():
    run("ls -l")