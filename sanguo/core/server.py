# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-16'

from django.conf import settings

class _Server(object):
    __slots__ = ['id', 'name', 'host', 'port', 'port_https', 'opened_date', 'active', 'test']
    def __init__(self):
        self.id = settings.SERVER_ID
        self.name = settings.SERVER_NAME
        self.host = settings.SERVER_IP
        self.port = settings.LISTEN_PORT_HTTP
        self.port_https = settings.LISTEN_PORT_HTTPS
        self.opened_date = settings.SERVER_OPEN_DATE
        self.test = settings.SERVER_TEST
        self.active = True

server = _Server()
