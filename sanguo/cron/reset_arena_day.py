# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import json

import uwsgidecorators

from cron.log import Logger

from core.arena import ArenaScoreManager
from core.attachment import make_standard_drop_from_template
from core.mail import Mail
from preset.data import ARENA_DAY_REWARD_TUPLE
from preset.settings import MAIL_ARENA_DAY_REWARD_CONTENT, MAIL_ARENA_DAY_REWARD_TITLE

# 只发送奖励

def _get_reward_by_score(score):
    for _score, _reward in ARENA_DAY_REWARD_TUPLE:
        if score >= _score:
            data = make_standard_drop_from_template()
            data['sycee'] = _reward.sycee
            data['gold'] = _reward.gold
            return json.dumps(data)

    return None

# 周一到周六21：30比武积分奖励

def main(signum):
    logger = Logger('reset_arena_day.log')

    arena_scores = ArenaScoreManager.get_all()
    amount = len(arena_scores)
    logger.write("Reset Arena Day: Start. chars amount: {0}".format(amount))

    for char_id, score in arena_scores:
        attachment = _get_reward_by_score(score)
        if not attachment:
            continue

        char_id = int(char_id)
        mail = Mail(char_id)
        mail.add(MAIL_ARENA_DAY_REWARD_TITLE, MAIL_ARENA_DAY_REWARD_CONTENT, attachment=attachment)

    logger.write("Reset Arena Day: Complete")
    logger.close()

uwsgidecorators.cron(30, 21, -1, -1, 1)(main)
uwsgidecorators.cron(30, 21, -1, -1, 2)(main)
uwsgidecorators.cron(30, 21, -1, -1, 3)(main)
uwsgidecorators.cron(30, 21, -1, -1, 4)(main)
uwsgidecorators.cron(30, 21, -1, -1, 5)(main)
uwsgidecorators.cron(30, 21, -1, -1, 6)(main)
