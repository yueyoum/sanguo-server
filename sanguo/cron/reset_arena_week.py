# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from _base import Logger

from apps.config.models import ArenaReward
from core.attachment import Attachment
from core.mongoscheme import MongoArenaTopRanks, MongoArenaWeek
from core.character import Char


TOP_RANKS = [1, 2, 3]
def reset():
    amount = MongoArenaWeek.objects.count()

    logger = Logger("reset_arena_week.log")
    logger.write("Reset Arena Week: Start. chars amount: {0}".format(amount))

    data = MongoArenaWeek.objects.all()
    MongoArenaWeek.objects.delete()

    reward_data = ArenaReward.all()

    for d in data:
        reward = ArenaReward.cache_obj(d.rank, reward_data)
        gold = reward.week_gold
        attachment = Attachment(d.id)
        attachment.save_to_attachment(3, gold=gold)

        if d.rank in TOP_RANKS:
            try:
                top = MongoArenaTopRanks.objects.get(id=d.rank)
            except DoesNotExist:
                top = MongoArenaTopRanks(id=d.rank)

            char_name = Char(d.id).cacheobj.name
            top.name = char_name
            top.save()

    logger.write("Reset Arena Week: Complete")
    logger.close()


if __name__ == '__main__':
    reset()
