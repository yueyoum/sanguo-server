# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import json

from _base import Logger
from core.mail import Mail
from core.mongoscheme import MongoUnion
from core.union.union import Union
from preset.data import UNION_BATTLE_REWARD
from preset.settings import (
    MAIL_UNION_BATTLE_REWARD_TITLE,
    MAIL_UNION_BATTLE_REWARD_CONTENT,
)

UNION_BATTLE_REWARD_TUPLE = UNION_BATTLE_REWARD.items()
UNION_BATTLE_REWARD_TUPLE.sort(key=lambda item: item[0])
LOWEST_UNION_BATTLE_RANK = max(UNION_BATTLE_REWARD.keys())


def _get_reward_by_rank(rank):

    for _rank, _reward in UNION_BATTLE_REWARD_TUPLE:
        if _rank >= rank:
            return {
                'union_contribute_points': _reward.contribute_points,
                'union_coin': _reward.coin
            }


def _send_reward(rank, mongo_union):
    data = _get_reward_by_rank(rank)
    contribute_points = data.pop('union_contribute_points')

    u = Union(mongo_union.owner)
    u.add_contribute_points(contribute_points)

    members = u.member_list

    attachment = json.dumps(data)
    for mid in members:
        m = Mail(mid)
        m.add(
            MAIL_UNION_BATTLE_REWARD_TITLE,
            MAIL_UNION_BATTLE_REWARD_CONTENT,
            attachment=attachment
        )


def reset():
    logger = Logger("union_reward_week.log")

    unions = MongoUnion.objects.all().order_by('-score')
    rank = 1
    for u in unions:
        if rank > LOWEST_UNION_BATTLE_RANK:
            break

        _send_reward(rank, u)
        rank+=1


    logger.write("Union Reward Week: Complete")
    logger.close()


if __name__ == '__main__':
    reset()
