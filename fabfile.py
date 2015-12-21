# -*- coding: utf-8 -*-

import os
import glob
from time import sleep
from fabric.api import *


#
# CMD_GIT_BRANCH = "git branch | sed -n '/\*/p' | sed -n 's/\* //p'"
#
# LOCAL_SERVER_PATH = "/home/wang/projects/sangou/server"
# LOCAL_HUB_PATH = "/home/wang/projects/sangou/hub"


# def get_local_server_branch():
#     with lcd(LOCAL_SERVER_PATH):
#         result = local(CMD_GIT_BRANCH, capture=True)
#         return result.stdout
#
#
# def get_local_hub_branch():
#     with lcd(LOCAL_HUB_PATH):
#         result = local(CMD_GIT_BRANCH, capture=True)
#         return result.stdout

#
# class Server(object):
#     PARENT_PATH = None
#     DIRS = None
#
#     def __init__(self):
#         self.local_branch = get_local_server_branch()
#
#     def run(self):
#         self.pull()
#         self.restart()
#
#     def pull(self):
#         for d in self.DIRS:
#             folder = os.path.join(self.PARENT_PATH, d)
#             with cd(folder):
#                 result = run(CMD_GIT_BRANCH)
#                 remote_branch = result.stdout
#                 if self.local_branch != remote_branch:
#                     abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))
#
#                 self.before_pull(folder)
#                 run("git pull")
#                 self.after_pull(folder)
#
#     def patch(self, f):
#         for d in self.DIRS:
#             with cd(os.path.join(self.PARENT_PATH, d)):
#                 run("git apply {0}".format(f))
#
#     def restart(self):
#         for d in self.DIRS:
#             folder = os.path.join(self.PARENT_PATH, d)
#             with cd(folder):
#                 self.before_restart(folder)
#                 run("./restart.sh")
#                 self.after_restart(folder)
#
#     def before_pull(self, folder):
#         # called before run git pull
#         pass
#
#     def after_pull(self, folder):
#         # called after run git pull
#         pass
#
#     def before_restart(self, folder):
#         # called before restart
#         pass
#
#     def after_restart(self, folder):
#         # called after restart
#         pass
#
#
# class Hub(object):
#     PATH = "/opt/sanguo/hub"
#
#     def __init__(self):
#         self.local_branch = get_local_hub_branch()
#
#     def run(self):
#         self.pull()
#         self.restart()
#
#     def pull(self):
#         with cd(self.PATH):
#             result = run(CMD_GIT_BRANCH)
#             remote_branch = result.stdout
#             if self.local_branch != remote_branch:
#                 abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))
#
#             self.before_pull()
#             run("git pull")
#             self.after_pull()
#
#     def restart(self):
#         with cd(self.PATH):
#             self.before_restart()
#             run("./restart.sh")
#             run("./restart_admin.sh")
#             self.after_restart()
#
#     def before_pull(self):
#         # called before run git pull
#         pass
#
#     def after_pull(self):
#         # called after run git pull
#         pass
#
#     def before_restart(self):
#         # called before restart
#         pass
#
#     def after_restart(self):
#         # called after restart
#         pass
#
#
# class ServerAiYingYong(Server):
#     PARENT_PATH = "/opt/sanguo"
#     DIRS = ["server%d" % i for i in range(1, 8 + 1)]
#
#
# class ServerJodo(Server):
#     PARENT_PATH = "/opt/sanguo"
#     DIRS = ["server%d" % i for i in range(1, 2 + 1)]
#
#
# class ServerInternal(Server):
#     PARENT_PATH = "/opt/sanguo"
#     DIRS = ["server%d" % i for i in range(1, 2 + 1)]
#
#
# @hosts("muzhi@192.168.1.100")
# def deploy_internal(target='all'):
#     hub = Hub()
#     server = ServerInternal()
#
#     if target == 'hub':
#         hub.run()
#     elif target == 'server':
#         server.run()
#     elif target == 'all':
#         hub.run()
#         server.run()
#     else:
#         abort("wrong target!")
#
#
# @hosts("developer@114.215.129.77:292")
# def deploy_testing(target='all'):
#     pass
#
#
# @hosts("developer@120.27.28.159:292")
# def deploy_wp(target='all'):
#     hub = Hub()
#     server = ServerAiYingYong()
#
#     if target == 'hub':
#         hub.run()
#     elif target == 'server':
#         server.run()
#     elif target == 'all':
#         hub.run()
#         server.run()
#     else:
#         abort("wrong target!")
#

# GET CFGDATA
def get_cfgdata(name):
    location = "/tmp/smb"
    local("mkdir -p {0}".format(location))
    with settings(warn_only=True):
        local("sudo mount -t cifs -o user=wang //192.168.1.100/public {0}".format(location))

    if name == 'None':
        pattern = os.path.join(location, "cfgdata", "cfgdata*.zip")

        fs = glob.glob(pattern)
        fs.sort(key=lambda x: -os.path.getmtime(x))
        return os.path.abspath(fs[0])

    f = os.path.join(location, "cfgdata", name)
    return f


class Version(object):
    def __init__(self, config_path):
        self.config_path = config_path

    def run(self, name, version):
        if name.startswith('/'):
            # local file
            f = name
        else:
            # remote file
            f = get_cfgdata(name)

        with cd(self.config_path):
            put(f, "cfgdata-{0}.zip".format(version))
            run("rm -f cfgdata.zip")
            run("ln -s cfgdata-{0}.zip cfgdata.zip".format(version))
            run('echo "{0}" > version.txt'.format(version))


# OK TO USE
@hosts("developer@120.27.28.159:292")
def upload_cfgdata_to_wp(name, version):
    Version("/opt/sanguo/update/config").run(name, version)
    sleep(1)
    with cd("/opt/sanguo/hub"):
        run("./restart.sh")

    sleep(1)
    with cd("/home/developer"):
        run("./pull.sh")
        run("./restart.sh")


# OK TO USE
@hosts("developer@120.27.41.22:292")
def upload_cfgdata_to_ios(name, version):
    Version("/opt/sanguo/update/config").run(name, version)
    sleep(1)
    with cd("/opt/sanguo/hub"):
        run("./restart.sh")

    sleep(1)
    with cd("/home/developer"):
        run("./pull.sh")
        run("./restart.sh")
