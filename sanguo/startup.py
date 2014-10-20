# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-30'

"""
Functions decorated by `startup` in this file will execute first when server start up.
"""


from django.conf import settings
from core.server import server
from utils.api import api_server_register, APIFailure

FUNCS = []

def startup(func):
    FUNCS.append(func)
    def deco(*args, **kwargs):
        return func(*args, **kwargs)
    return deco


@startup
def server_register(status=1):
    data = {
        'id': server.id,
        'name': server.name,
        'status': status,
        'host': server.host,
        'port': server.port,
        'port_https': server.port_https,
    }

    res = api_server_register(data)
    if res['ret'] != 0:
        raise APIFailure("api_server_register, error: {0}".format(res))

    version = res['data']['version']
    settings.SERVER_VERSION = version

    print "==== START ===="
    print "version: {0}".format(settings.SERVER_VERSION)


def main():
    for f in FUNCS:
        f()

