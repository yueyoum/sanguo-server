# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-25'

import os
import cPickle


class GameSession(object):
    __slots__ = ['account_id', 'server_id', 'char_id', 'login_id']
    def __init__(self, account_id, server_id, char_id):
        self.account_id = account_id
        self.server_id = server_id
        self.char_id = char_id
        self.login_id = os.urandom(10)

def session_dumps(obj):
    return cPickle.dumps(obj, 2)

def session_loads(data):
    return cPickle.loads(data)
