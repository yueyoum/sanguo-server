# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-17'

import os
import glob
from time import sleep
from fabric.api import *

CMD_GIT_BRANCH = "git branch | sed -n '/\*/p' | sed -n 's/\* //p'"

LOCAL_SERVER_PATH = "/home/wang/projects/sangou/server"
LOCAL_HUB_PATH = "/home/wang/projects/sangou/hub"

def get_local_server_branch():
    with lcd(LOCAL_SERVER_PATH):
        result = local(CMD_GIT_BRANCH, capture=True)
        return result.stdout

def get_local_hub_branch():
    with lcd(LOCAL_HUB_PATH):
        result = local(CMD_GIT_BRANCH, capture=True)
        return result.stdout


def push_server(remote):
    with lcd(LOCAL_SERVER_PATH):
        cmd = "git push {0} {1}".format(remote, get_local_server_branch())
        local(cmd)


def push_hub(remote):
    with lcd(LOCAL_HUB_PATH):
        cmd = "git push {0} {1}".format(remote, get_local_server_branch())
        local(cmd)


class Server(object):
    def __init__(self, local_branch, parent_path, dirs):
        self.local_branch = local_branch
        self.parent_path = parent_path
        self.dirs = dirs

    def run(self):
        self.pull()
        self.restart()


    def pull(self):
        for d in self.dirs:
            with cd(os.path.join(self.parent_path, d)):
                result = run(CMD_GIT_BRANCH)
                remote_branch = result.stdout
                if self.local_branch != remote_branch:
                    abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))

                run("git pull")

    def restart(self):
        for d in self.dirs:
            with cd(os.path.join(self.parent_path, d)):
                run("./restart.sh")

class Hub(object):
    def __init__(self, path):
        self.local_branch = get_local_hub_branch()
        self.path = path

    def restart(self):
        with cd(self.path):
            run("kill -HUP `cat run/uwsgi.pid`")



@hosts("muzhi@192.168.1.100")
def deploy_server_on_internal():
    server = Server(
        get_local_server_branch(),
        "/opt/sanguo",
        ["server1",]
    )
    server.run()

@hosts("developer@114.215.129.77")
def deploy_server_on_testing():
    server = Server(
        get_local_server_branch(),
        "/opt/sanguo",
        ["server",]
    )
    server.run()




# GET CFGDATA
def get_cfgdata():
    dir = "/tmp/smb"
    local("mkdir -p {0}".format(dir))
    with settings(warn_only=True):
        local("sudo mount -t cifs -o user=wang //192.168.1.100/public {0}".format(dir))

    pattern = os.path.join(dir, "cfgdata", "cfgdata*.zip")

    fs = glob.glob(pattern)
    fs.sort(key=lambda x: -os.path.getmtime(x))
    return os.path.abspath(fs[0])

class Version(object):
    def __init__(self, config_path):
        self.config_path = config_path

    def run(self, version):
        with cd(self.config_path):
            put(get_cfgdata(), "cfgdata-{0}.zip".format(version))
            run("rm -f cfgdata.zip")
            run("ln -s cfgdata-{0}.zip cfgdata.zip".format(version))
            run('echo "{0}" > version.txt'.format(version))



@hosts("muzhi@192.168.1.100")
def upload_cfgdata_to_internal(version):
    Version("/opt/sanguo/update/config").run(version)
    sleep(1)
    Hub("/opt/sanguo/hub").restart()
    sleep(1)
    Server(
        get_local_server_branch(),
        "/opt/sanguo",
        ["server1",]
    ).restart()


@hosts("developer@114.215.129.77")
def upload_cfgdata_to_testing(version):
    Version("/opt/sanguo/update/config").run(version)
    sleep(1)
    Hub("/opt/sanguo/hub").restart()
    sleep(1)
    Server(
        get_local_server_branch(),
        "/opt/sanguo",
        ["server",]
    ).restart()


