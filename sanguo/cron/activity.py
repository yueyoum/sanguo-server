# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       activity
Date Created:   2016-02-26 15-16
Description:

"""

import traceback
import uwsgidecorators
from cron.log import Logger

from core.mongoscheme import MongoCharacter

from core.activity import Activity22001


@uwsgidecorators.cron(0, 0, -1, -1, -1, target='spooler')
def send_vip_reward(signum):
    logger = Logger("send_vip_reward.log")
    logger.write("Start")

    try:
        docs = MongoCharacter._get_collection().find(
            {'vip': {'$gte': 6}},
            {'_id': 1}
        )

        for doc in docs:
            char_id = doc['_id']

            ac = Activity22001(char_id)
            if ac.is_valid():
                ac.send_mail()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Done")
    finally:
        logger.close()
