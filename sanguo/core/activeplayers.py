# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/24/14'

from apps.server.models import Server as ModelServer
from core.drives import redis_client_two
from utils.timezone import utc_timestamp

ACTIVE_USER_KEY = 'active_players'
ACTIVE_TIME_DIFF = 30 * 60

class ActivePlayers(object):
    def __init__(self, server_id):
        self.key = '{0}:{1}'.format(ACTIVE_USER_KEY, server_id)

    def set(self, char_id):
        redis_client_two.zadd(self.key, char_id, utc_timestamp())

    def get_list(self):
        players = redis_client_two.zrange(self.key, 0, -1)
        return [int(i) for i in players]

    def clean(self):
        now = utc_timestamp()
        players = redis_client_two.zrange(self.key, 0, -1, withscores=True)

        expired = []
        for p, t in players:
            if now - t > ACTIVE_TIME_DIFF:
                expired.append(int(p))

        redis_client_two.zrem(self.key, *expired)
        return len(expired)

    @classmethod
    def clean_all(cls):
        server_ids = ModelServer.all_ids()
        amount = 0
        for sid in server_ids:
            ap = cls(sid)
            res = ap.clean()
            amount += res
        return amount

