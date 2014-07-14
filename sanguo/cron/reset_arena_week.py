# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'


from _base import Logger

import json
from mongoengine import DoesNotExist
import arrow

from core.attachment import make_standard_drop_from_template
from core.mongoscheme import MongoArenaTopRanks, MongoArenaWeek
from core.character import Char
from core.mail import Mail
from core.achievement import Achievement

from preset.data import ARENA_DAY_REWARD_TUPLE, ARENA_WEEK_REWARD_TUPLE
from preset.settings import MAIL_ARENA_WEEK_REWARD_CONTENT, MAIL_ARENA_WEEK_REWARD_TITLE

def _set_mongo_week(char_id, rank):
    try:
        week = MongoArenaWeek.objects.get(id=char_id)
    except DoesNotExist:
        week = MongoArenaWeek(id=char_id)

    week.score = 0
    week.rank = rank
    week.save()

    Achievement(char_id).trig(10, rank)


def _set_top_ranks(*top_ids):
    for index, _id in enumerate(top_ids):
        name = Char(_id).mc.name
        rank = index + 1
        try:
            top = MongoArenaTopRanks.objects.get(id=rank)
        except DoesNotExist:
            top = MongoArenaTopRanks(id=rank)

        top.name = name
        top.save()


def _get_reward_by_rank(rank):
    data = make_standard_drop_from_template()
    for _rank, _reward in ARENA_DAY_REWARD_TUPLE:
        if rank >= _rank:
            data['sycee'] = _reward.sycee * 2
            data['gold'] = _reward.gold * 2
            break

    for _rank, _reward in ARENA_WEEK_REWARD_TUPLE:
        if rank >= _rank and _reward.stuff_id:
            data['stuffs'] = [(_reward.stuff_id, 1)]
            data.update({'stuffs': [(_reward.stuff_id, 1)]})
            break

    if data:
        return json.dumps(data)
    return None


def reset():
    amount = MongoArenaWeek.objects.count()

    logger = Logger("reset_arena_week.log")
    logger.write("Reset Arena Week: Start. chars amount: {0}".format(amount))

    mongo_week_data = MongoArenaWeek.objects.all()
    week_data = [(d.id, d.score) for d in mongo_week_data]

    week_data.sort(key=lambda item: -item[1])
    for index, data in enumerate(week_data):
        rank = index + 1
        char_id = data[0]

        _set_mongo_week(char_id, rank)

    #  设置完MongoWeek 后，设置TopRanks
    top_ids = [_id for _id, _ in week_data[:3]]
    _set_top_ranks(*top_ids)

    # 最后发送奖励
    for index, data in enumerate(week_data):
        rank = index + 1
        char_id = data[0]

        attachment = _get_reward_by_rank(rank)
        if not attachment:
            continue

        mail = Mail(char_id)
        create_at = arrow.utcnow().format('YYYY-MM-DD HH:mm:ss')
        mail.add(MAIL_ARENA_WEEK_REWARD_TITLE, MAIL_ARENA_WEEK_REWARD_CONTENT, create_at, attachment=attachment)

    logger.write("Reset Arena Week: Complete")
    logger.close()


if __name__ == '__main__':
    reset()
