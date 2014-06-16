# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-16'

from django.conf import settings
from utils.api import api_server_list

NODE_ID = settings.NODE_ID

SERVERS = {}

def get_server_list():
    global SERVERS
    res = api_server_list({})
    ALL_SERVERS = res['data']
    SERVERS = {}
    for k, v in ALL_SERVERS.iteritems():
        if v['node'] == NODE_ID:
            SERVERS[int(k)] = v

get_server_list()
