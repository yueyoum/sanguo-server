# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-16'

from django.conf import settings
from libs.functional import get_ipv4_address

class _Server(object):
    __slots__ = ['id', 'name', 'ip', 'port', 'port_https']
    def __init__(self):
        self.id = settings.SERVER_ID
        self.name = settings.SERVER_NAME
        self.ip = get_ipv4_address()
        self.port = settings.LISTEN_PORT_HTTP
        self.port_https = settings.LISTEN_PORT_HTTPS

server = _Server()
