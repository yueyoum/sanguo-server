# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import json

import uwsgidecorators

from cron.log import Logger
from core.character import Char
from core.mail import Mail
from core.arena import REDIS_ARENA_KEY
from core.drives import redis_client_persistence
from core.achievement import Achievement
from core.activity import ActivityStatic
from core.item import Item
from preset.data import ARENA_WEEK_REWARD
from preset.settings import (
    MAIL_ARENA_WEEK_REWARD_CONTENT,
    MAIL_ARENA_WEEK_REWARD_TITLE,
    ARENA_RANK_LINE,
)


ARENA_WEEK_REWARD_TUPLE = ARENA_WEEK_REWARD.items()
ARENA_WEEK_REWARD_TUPLE.sort(key=lambda item: -item[0])

ARENA_WEEK_REWARD_LOWEST_RANK = max(ARENA_WEEK_REWARD.keys())

# 周日21：30发送周比武奖励


def _get_reward_by_rank(rank):
    data = None

    for _rank, _reward in ARENA_WEEK_REWARD_TUPLE:
        if _rank >= rank:
            data = Item.get_sutff_drop(_reward.stuff)
            break

    if data:
        return json.dumps(data)
    return None



@uwsgidecorators.cron(30, 21, -1, -1, 0)
def reset(signum):
    amount = redis_client_persistence.zcard(REDIS_ARENA_KEY)

    logger = Logger("reset_arena_week.log")
    logger.write("Reset Arena Week: Start. chars amount: {0}".format(amount))

    score_data = redis_client_persistence.zrevrange(REDIS_ARENA_KEY, 0, ARENA_WEEK_REWARD_LOWEST_RANK-1, withscores=True)

    rank_data = []
    for char_id, score in score_data:
        rank_data.append( (int(char_id), score, Char(int(char_id)).power) )

    rank_data.sort(key=lambda item: (-item[1], -item[2]))


    # 发送奖励
    for index, data in enumerate(rank_data):
        rank = index + 1
        char_id = data[0]
        score = data[1]

        ActivityStatic(char_id).send_mail()

        if score < ARENA_RANK_LINE:
            continue

        achievement = Achievement(char_id)
        achievement.trig(10, rank)

        attachment = _get_reward_by_rank(rank)
        if not attachment:
            continue

        mail = Mail(char_id)
        mail.add(MAIL_ARENA_WEEK_REWARD_TITLE, MAIL_ARENA_WEEK_REWARD_CONTENT, attachment=attachment)

    logger.write("Reset Arena Week: Complete")
    logger.close()
