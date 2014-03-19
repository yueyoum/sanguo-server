# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from _base import Logger
from apps.config.models import ArenaReward
from core.character import Char
from core.drives import redis_client_two
from core.attachment import Attachment
from core.mongoscheme import MongoArena, MongoArenaDay, MongoArenaWeek


# 发送奖励，将日积分累加到周积分上，并且将日积分归零

def reset():
    amount = MongoArenaDay.objects.count()

    logger = Logger('reset_arena_day.log')
    logger.write("Reset Arena Day: Start. chars amount: {0}".format(amount))

    arena_day = MongoArenaDay.objects.all()
    MongoArenaDay.objects.delete()

    # reward_data = ArenaReward.all()

    chars_data = []
    for ad in arena_day:
        char_id = ad.id
        char_score = ad.score
        char_power = Char(char_id).power
        chars_data.append((char_id, char_score, char_power))

    chars_data.sort(key=lambda item: (-item[1], -item[2]))

    for index, data in enumerate(chars_data):
        rank = index + 1
        char_id = data[0]
        score = data[1]

        try:
            arena_week = MongoArenaWeek.objects.get(id=char_id)
        except DoesNotExist:
            arena_week = MongoArenaWeek(id=char_id)
            arena_week.score = 0

        arena_week.score += score
        arena_week.rank = rank
        arena_week.save()

        # FIXME reward
        attachment = Attachment(char_id)
        attachment.save_to_attachment(2, gold=100)


    logger.write("Reset Arena Day: Complete")
    logger.close()

if __name__ == '__main__':
    reset()
