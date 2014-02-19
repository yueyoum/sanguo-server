# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from _base import Logger

from apps.config.models import ArenaReward
from core.drives import redis_client_two
from core.attachment import Attachment
from core.mongoscheme import MongoArenaTopRanks
from core.character import Char

from core.arena import REDIS_WEEK_KEY

TOP_RANKS = [1, 2, 3]
def reset():
    amount = redis_client_two.zcard(REDIS_WEEK_KEY)
    logger = Logger("reset_arena_week.log")
    logger.write("Reset Arena Week: Start. chars amount: {0}".format(amount))

    data = redis_client_two.zrevrange(REDIS_WEEK_KEY, 0, -1)
    redis_client_two.delete(REDIS_WEEK_KEY)


    reward_data = ArenaReward.all()
    for index, char_id in data:
        rank = index + 1
        char_id = int(char_id)

        cache_char = Char(char_id).cacheobj
        char_name = cache_char.name

        # 记录前三甲
        reward = ArenaReward.cache_obj(rank, reward_data)
        if rank in TOP_RANKS:
            try:
                top = MongoArenaTopRanks.objects.get(id=rank)
            except DoesNotExist:
                top = MongoArenaTopRanks(id=rank)
            top.name = char_name
            top.save()

        gold = reward.week_gold
        attachment = Attachment(char_id)
        attachment.save_to_attachment(3, gold=gold)

    logger.write("Reset Arena Week: Complete")


if __name__ == '__main__':
    reset()
