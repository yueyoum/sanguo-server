# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from _base import Logger

from core.attachment import Attachment
from core.mongoscheme import MongoArenaTopRanks, MongoArenaWeek
from core.character import Char
from core.achievement import Achievement

from preset.data import ARENA_REWARD

def _get_reward(rank):
    for k, v in ARENA_REWARD.items():
        if rank >= k:
            return v


TOP_RANKS = [1, 2, 3]
def reset():
    amount = MongoArenaWeek.objects.count()

    logger = Logger("reset_arena_week.log")
    logger.write("Reset Arena Week: Start. chars amount: {0}".format(amount))

    data = MongoArenaWeek.objects.all()
    MongoArenaWeek.objects.delete()


    for d in data:
        reward = _get_reward(d.rank)
        gold = reward.week_gold
        attachment = Attachment(d.id)
        attachment.save_to_attachment(3, gold=gold)

        achievement = Achievement(d.id)
        achievement.trig(10, d.rank)

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
