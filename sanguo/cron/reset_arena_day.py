# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from _base import Logger
from apps.config.models import ArenaReward
from core.drives import redis_client_two
from core.attachment import Attachment

from core.arena import REDIS_DAY_KEY, REDIS_WEEK_KEY

# 发送奖励，将日积分累加到周积分上，并且将日积分归零

def reset():
    amount = redis_client_two.zcard(REDIS_DAY_KEY)
    logger = Logger('reset_arena_day.log')
    logger.write("Reset Arena Day: Start. chars amount: {0}".format(amount))

    data = redis_client_two.zrevrange(REDIS_DAY_KEY, 0, -1, withscores=True)
    redis_client_two.delete(REDIS_DAY_KEY)

    reward_data = ArenaReward.all()

    pipe = redis_client_two.pipeline()
    for index, d in enumerate(data):
        rank = index + 1
        char_id = int(d[0])
        score = int(d[1])

        reward = ArenaReward.cache_obj(rank, reward_data)
        gold = reward.day_gold

        attachment = Attachment(char_id)
        attachment.save_to_attachment(2, gold=gold)

        pipe.zincrby(REDIS_WEEK_KEY, char_id, score)

    pipe.execute()
    logger.write("Reset Arena Day: Complete")
    logger.close()

if __name__ == '__main__':
    reset()
