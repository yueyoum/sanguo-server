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
    PARENT_PATH = None
    DIRS = None
    def __init__(self):
        self.local_branch = get_local_server_branch()

    def run(self):
        self.pull()
        self.restart()


    def pull(self):
        for d in self.DIRS:
            folder = os.path.join(self.PARENT_PATH, d)
            with cd(folder):
                result = run(CMD_GIT_BRANCH)
                remote_branch = result.stdout
                if self.local_branch != remote_branch:
                    abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))

                self.before_pull(folder)
                run("git pull")
                self.after_pull(folder)

    def patch(self, f):
        for d in self.DIRS:
            with cd(os.path.join(self.PARENT_PATH, d)):
                run("git apply {0}".format(f))

    def restart(self):
        for d in self.DIRS:
            folder = os.path.join(self.PARENT_PATH, d)
            with cd(folder):
                self.before_restart(folder)
                run("./restart.sh")
                self.after_restart(folder)


    def before_pull(self, folder):
        # called before run git pull
        pass

    def after_pull(self, folder):
        # called after run git pull
        pass

    def before_restart(self, folder):
        # called before restart
        pass

    def after_restart(self, folder):
        # called after restart
        pass



class Hub(object):
    def __init__(self, path):
        self.local_branch = get_local_hub_branch()
        self.path = path

    def run(self):
        self.pull()
        self.restart()

    def pull(self):
        with cd(self.path):
            result = run(CMD_GIT_BRANCH)
            remote_branch = result.stdout
            if self.local_branch != remote_branch:
                abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))

            run("git pull")

    def restart(self):
        with cd(self.path):
            run("./restart.sh")
            run("./restart_admin.sh")




class ServerAiYingYong(Server):
    PARENT_PATH = "/opt/sanguo"
    DIRS = ["server%d" % i for i in range(1, 5+1)]

    def before_pull(self, folder):
        run("git checkout sanguo/preset/fixtures/purchase.json")

    def after_pull(self, folder):
        run("cp /home/developer/backup/purchase.json sanguo/preset/fixtures/")


class ServerJodo(Server):
    PARENT_PATH = "/opt/sanguo"
    DIRS = ["server%d" % i for i in range(1, 2+1)]



@hosts("muzhi@192.168.1.100")
def deploy_internal(target='all'):
    hub = Hub("/opt/sanguo/hub")
    server = Server("/opt/sanguo", ["server1"])

    if target == 'hub':
        hub.run()
    elif target == 'server':
        server.run()
    elif target == 'all':
        hub.run()
        server.run()
    else:
        abort("wrong target!")


@hosts("developer@114.215.129.77:292")
def deploy_testing(target='all'):
    hub = Hub("/opt/sanguo/hub")
    server = Server("/opt/sanguo", ["server"])

    if target == 'hub':
        hub.run()
    elif target == 'server':
        server.run()
    elif target == 'all':
        hub.run()
        server.run()
    else:
        abort("wrong target!")


@hosts("developer@115.28.201.238:292")
def deploy_91_ios(target='all'):
    hub = Hub("/opt/sanguo/hub")
    server = Server("/opt/sanguo", ["server", "server2",])

    if target == 'hub':
        hub.run()
    elif target == 'server':
        server.run()
    elif target == 'all':
        hub.run()
        server.run()
    else:
        abort("wrong target!")


@hosts("developer@120.27.28.159:292")
def deploy_wp(target='all'):
    hub = Hub("/opt/sanguo/hub")
    server = ServerAiYingYong()

    if target == 'hub':
        hub.run()
    elif target == 'server':
        server.run()
    elif target == 'all':
        hub.run()
        server.run()
    else:
        abort("wrong target!")


# GET CFGDATA
def get_cfgdata(name=None):
    dir = "/tmp/smb"
    local("mkdir -p {0}".format(dir))
    with settings(warn_only=True):
        local("sudo mount -t cifs -o user=wang //192.168.1.100/public {0}".format(dir))

    if name is None:
        pattern = os.path.join(dir, "cfgdata", "cfgdata*.zip")

        fs = glob.glob(pattern)
        fs.sort(key=lambda x: -os.path.getmtime(x))
        return os.path.abspath(fs[0])

    f = os.path.join(dir, "cfgdata", name)
    return f


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
        "/opt/sanguo",
        ["server1",]
    ).restart()


@hosts("developer@114.215.129.77:292")
def upload_cfgdata_to_testing(version):
    Version("/opt/sanguo/update/config").run(version)
    sleep(1)
    Hub("/opt/sanguo/hub").restart()
    sleep(1)
    Server(
        "/opt/sanguo",
        ["server",]
    ).restart()


# OK TO USE
@hosts("developer@120.27.28.159:292")
def upload_cfgdata_to_wp(version):
    Version("/opt/sanguo/update/config").run(version)
    sleep(1)
    Hub("/opt/sanguo/hub").run()
    sleep(1)
    ServerAiYingYong().run()

# OK TO USE
@hosts("developer@203.88.160.14:292")
def upload_cfgdata_to_jodo(version):
    Version("/opt/sanguo/update/config").run(version)
    sleep(1)
    Hub("/opt/sanguo/hub").run()
    sleep(1)
    ServerJodo().run()



@hosts("muzhi@192.168.1.100")
def upload_to_internal(f):
    put(f, "/tmp")

@hosts("developer@115.28.201.238:292")
def upload_to_91_ios(f):
    put(f, "/tmp")


@hosts("muzhi@192.168.1.100")
def hotfix_on_internal(f):
    remote_f = "/tmp/{0}".format(os.path.basename(f))
    put(f, remote_f)
    s = Server("/opt/sanguo", ["server1"])
    s.patch(remote_f)
    s.restart()

@hosts("developer@115.28.201.238:292")
def hotfix_on_91_ios(f):
    remote_f = "/tmp/{0}".format(os.path.basename(f))
    put(f, remote_f)
    s = Server("/opt/sanguo", ["server", "server2"])
    s.patch(remote_f)
    s.restart()
