# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-17'

import os
from fabric.api import *

CMD_GIT_BRANCH = "git branch | sed -n '/\*/p' | sed -n 's/\* //p'"

def get_local_branch():
    lcd("/home/wang/projects/sangou/server")
    result = local(CMD_GIT_BRANCH, capture=True)
    return result.stdout


def push(remote):
    cmd = "git push {0} {1}".format(remote, get_local_branch())
    local(cmd)


class Server(object):
    def __init__(self, local_branch, parent_path, dirs):
        self.local_branch = local_branch
        self.parent_path = parent_path
        self.dirs = dirs


    def run(self):
        for d in self.dirs:
            with cd(os.path.join(self.parent_path, d)):
                result = run(CMD_GIT_BRANCH)
                remote_branch = result.stdout
                if self.local_branch != remote_branch:
                    abort("local branch: {0} != remote branch: {1}".format(self.local_branch, remote_branch))

                run("git pull")
                run("kill -HUP `cat sanguo/run/uwsgi.pid`")



@hosts("muzhi@192.168.1.100")
def deploy_server_on_internal():
    server = Server(
        get_local_branch(),
        "/opt/sanguo",
        ["server1",]
    )
    server.run()

@hosts("developer@114.215.129.77")
def deploy_server_on_testing():
    server = Server(
        get_local_branch(),
        "/opt/sanguo",
        ["server",]
    )
    server.run()
