# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'


from _base import Logger

import json
from mongoengine import DoesNotExist
import arrow

from core.drives import redis_client
from core.character import Char
from core.attachment import make_standard_drop_from_template
from core.mongoscheme import MongoArenaWeek
from core.mail import Mail
from core.arena import REDIS_DAY_KEY

from preset.data import ARENA_DAY_REWARD_TUPLE
from preset.settings import MAIL_ARENA_DAY_REWARD_CONTENT, MAIL_ARENA_DAY_REWARD_TITLE

# 发送奖励，将日积分累加到周积分上，并且将日积分归零

def _add_to_week(char_id, score):
    try:
        mongo_week = MongoArenaWeek.objects.get(id=char_id)
    except DoesNotExist:
        mongo_week = MongoArenaWeek(id=char_id)
        mongo_week.score = 0
        mongo_week.rank = 0

    mongo_week.score += score
    mongo_week.save()


def _get_reward_by_rank(rank):
    for _rank, _reward in ARENA_DAY_REWARD_TUPLE:
        if rank >= _rank:
            data = make_standard_drop_from_template()
            data['sycee'] = _reward.sycee
            data['gold'] = _reward.gold
            return json.dumps(data)

    return None


def reset():
    logger = Logger('reset_arena_day.log')

    amount = redis_client.zcard(REDIS_DAY_KEY)
    logger.write("Reset Arena Day: Start. chars amount: {0}".format(amount))

    arena_day_scores = redis_client.zrange(REDIS_DAY_KEY, 0, -1, withscores=True)
    redis_client.delete(REDIS_DAY_KEY)

    chars_data = []

    for char_id, score in arena_day_scores:
        char_id = int(char_id)
        score = int(score)
        _add_to_week(char_id, score)

        chars_data.append((char_id, score, Char(char_id).power))

    # 将日积分累加到周记录上后
    # 排名后发送日奖励
    chars_data.sort(key=lambda item: (-item[1], -item[2]))

    for index, data in enumerate(chars_data):
        rank = index + 1
        char_id = data[0]

        attachment = _get_reward_by_rank(rank)
        if not attachment:
            continue

        create_at = arrow.utcnow().format('YYYY-MM-DD HH:mm:ss')
        mail = Mail(char_id)
        mail.add(MAIL_ARENA_DAY_REWARD_TITLE, MAIL_ARENA_DAY_REWARD_CONTENT, create_at, attachment=attachment)

    logger.write("Reset Arena Day: Complete")
    logger.close()

if __name__ == '__main__':
    reset()
