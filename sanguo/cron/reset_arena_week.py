# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import json

import uwsgidecorators

from cron.log import Logger

from core.arena import ArenaScoreManager
from core.character import Char
from core.mail import Mail
from core.achievement import Achievement
from core.attachment import make_standard_drop_from_template
from core.activity import ActivityStatic
from preset.data import ARENA_WEEK_REWARD, ACTIVITY_STATIC, ACTIVITY_STATIC_CONDITIONS
from preset.settings import (
    MAIL_ARENA_WEEK_REWARD_CONTENT,
    MAIL_ARENA_WEEK_REWARD_TITLE,
    ARENA_RANK_LINE,
)


ARENA_WEEK_REWARD_TUPLE = ARENA_WEEK_REWARD.items()
ARENA_WEEK_REWARD_TUPLE.sort(key=lambda item: item[0])

ARENA_WEEK_REWARD_LOWEST_RANK = max(ARENA_WEEK_REWARD.keys())

# 周日21：30发送周比武奖励

def _get_reward_by_rank(rank):
    for _rank, _reward in ARENA_WEEK_REWARD_TUPLE:
        if rank <= _rank:
            drop = make_standard_drop_from_template()
            drop['stuffs'] = [(_reward.stuff, 1)]
            return drop

    return None


def get_rank_data(lowest_rank):
    # lowest_rank 最低排名，可以视为按照score从高到底排序后，最多要取多少人
    score_data = ArenaScoreManager.get_all_desc(lowest_rank)

    # 对于相同积分的人，用战斗力排序
    rank_data = []
    for char_id, score in score_data:
        rank_data.append( (char_id, score, Char(char_id).power) )

    rank_data.sort(key=lambda item: (-item[1], -item[2]))
    return rank_data



@uwsgidecorators.cron(30, 21, -1, -1, 0)
def reset(signum):
    logger = Logger("reset_arena_week.log")

    # 每周奖励
    rank_data = get_rank_data(ARENA_WEEK_REWARD_LOWEST_RANK)

    for index, data in enumerate(rank_data):
        rank = index + 1
        char_id = data[0]
        score = data[1]

        if score < ARENA_RANK_LINE:
            continue

        reward = _get_reward_by_rank(rank)
        if not reward:
            continue

        mail = Mail(char_id)
        mail.add(
            MAIL_ARENA_WEEK_REWARD_TITLE,
            MAIL_ARENA_WEEK_REWARD_CONTENT,
            attachment=json.dumps(reward))

    logger.write("Reset Arena Week: Complete")
    logger.close()

    # 成就
    rank_data = get_rank_data(None)
    for index, data in enumerate(rank_data):
        rank = index + 1
        char_id = data[0]

        achievement = Achievement(char_id)
        achievement.trig(10, rank)


    # 开服比武奖励
    _activity_anera_values = []
    for _ac in ACTIVITY_STATIC_CONDITIONS.values():
        if _ac.activity_id == 4001:
            _activity_anera_values.append(_ac.condition_value)

    LOWEST_RANK = max(_activity_anera_values)
    rank_data = get_rank_data(LOWEST_RANK)
    for index, data in enumerate(rank_data):
        char_id = data[0]

        ActivityStatic(char_id).trig(4001)
