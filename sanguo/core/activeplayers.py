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
