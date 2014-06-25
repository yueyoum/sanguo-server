# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/24/14'

import arrow

from core.server import SERVERS
from core.drives import redis_client_two

from preset.settings import PLAYER_ON_LINE_TIME_TO_ALIVE

ACTIVE_USER_KEY = 'active_players'

class ActivePlayers(object):
    def __init__(self, server_id):
        self.key = '{0}:{1}'.format(ACTIVE_USER_KEY, server_id)

    def set(self, char_id):
        now = arrow.utcnow().timestamp
        redis_client_two.zadd(self.key, char_id, now)

    def get_list(self):
        players = redis_client_two.zrange(self.key, 0, -1)
        return [int(i) for i in players]

    @property
    def amount(self):
        return redis_client_two.zcard(self.key)

    def clean(self):
        now = arrow.utcnow().timestamp
        limit = now - PLAYER_ON_LINE_TIME_TO_ALIVE
        cleaned_amount = redis_client_two.zremrangebyscore(self.key, '-inf', limit)
        return cleaned_amount


    @classmethod
    def clean_all(cls):
        server_ids = SERVERS.keys()

        result = {}
        for sid in server_ids:
            ap = cls(sid)
            res = ap.clean()

            result[sid] = {
                'cleaned': res,
                'remained': ap.amount
            }

        return result


PLAYER_LOGIN_ID_KEY = 'login_id:{0}'
class Player(object):
    __slots__ = ['char_id', 'key']
    def __init__(self, char_id):
        self.char_id = char_id
        self.key = PLAYER_LOGIN_ID_KEY.format(char_id)

    def set_login_id(self, login_id):
        redis_client_two.setex(self.key, login_id, 3600)

    def get_login_id(self):
        return redis_client_two.get(self.key)
