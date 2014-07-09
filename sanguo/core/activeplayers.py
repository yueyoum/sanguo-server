# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/24/14'

import arrow

from core.server import server
from core.drives import redis_client

from preset.settings import PLAYER_ON_LINE_TIME_TO_ALIVE

ACTIVE_USER_KEY = 'active_players'

class ActivePlayers(object):
    def __init__(self):
        self.key = '{0}:{1}'.format(ACTIVE_USER_KEY, server.id)

    def set(self, char_id):
        now = arrow.utcnow().timestamp
        redis_client.zadd(self.key, char_id, now)

    def get_list(self):
        players = redis_client.zrange(self.key, 0, -1)
        return [int(i) for i in players]

    @property
    def amount(self):
        return redis_client.zcard(self.key)

    def clean(self):
        now = arrow.utcnow().timestamp
        limit = now - PLAYER_ON_LINE_TIME_TO_ALIVE
        cleaned_amount = redis_client.zremrangebyscore(self.key, '-inf', limit)
        return {'cleaned': cleaned_amount, 'remained': self.amount}


PLAYER_LOGIN_ID_KEY = 'login_id:{0}'
class Player(object):
    __slots__ = ['char_id', 'key']
    def __init__(self, char_id):
        self.char_id = char_id
        self.key = PLAYER_LOGIN_ID_KEY.format(char_id)

    def set_login_id(self, login_id):
        redis_client.setex(self.key, login_id, 3600)

    def get_login_id(self):
        return redis_client.get(self.key)
