# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import traceback

import uwsgidecorators

from cron.log import Logger
from core.mongoscheme import MongoCharacter
from core.plunder import Plunder


# 1点到8点之间不增加，其他时段每半小时增加一次

def add_times(signum):
    logger = Logger('add_plunder_times.log')
    logger.write("Start")


    chars = MongoCharacter.objects.all()
    for char in chars:
        plunder = Plunder(char.id)
        try:
            plunder.change_current_plunder_times(change_value=1, allow_overflow=False)
        except:
            logger.error(traceback.format_exc())

    logger.write("add done")
    logger.close()



@uwsgidecorators.cron(0, 0, -1, -1, -1, target="mule")
def reset_times(signum):
    logger = Logger("plunder_reset_times.log")
    logger.write("Start")

    try:
        Plunder.cron_job()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("done")
    finally:
        logger.close()


# 00:00 / 00:30
uwsgidecorators.cron(-30, 0,  -1, -1, -1, target="mule")(add_times)
# 08:00 / 08:30
uwsgidecorators.cron(-30, 8,  -1, -1, -1, target="mule")(add_times)
# 09:00 / 09:30
uwsgidecorators.cron(-30, 9,  -1, -1, -1, target="mule")(add_times)
# 10:00 / 10:30
uwsgidecorators.cron(-30, 10, -1, -1, -1, target="mule")(add_times)
# 11:00 / 11:30
uwsgidecorators.cron(-30, 11, -1, -1, -1, target="mule")(add_times)
# 12:00 / 12:30
uwsgidecorators.cron(-30, 12, -1, -1, -1, target="mule")(add_times)
# 13:00 / 13:30
uwsgidecorators.cron(-30, 13, -1, -1, -1, target="mule")(add_times)
# 14:00 / 14:30
uwsgidecorators.cron(-30, 14, -1, -1, -1, target="mule")(add_times)
# 15:00 / 15:30
uwsgidecorators.cron(-30, 15, -1, -1, -1, target="mule")(add_times)
# 16:00 / 16:30
uwsgidecorators.cron(-30, 16, -1, -1, -1, target="mule")(add_times)
# 17:00 / 17:30
uwsgidecorators.cron(-30, 17, -1, -1, -1, target="mule")(add_times)
# 18:00 / 18:30
uwsgidecorators.cron(-30, 18, -1, -1, -1, target="mule")(add_times)
# 19:00 / 19:30
uwsgidecorators.cron(-30, 19, -1, -1, -1, target="mule")(add_times)
# 20:00 / 20:30
uwsgidecorators.cron(-30, 20, -1, -1, -1, target="mule")(add_times)
# 21:00 / 21:30
uwsgidecorators.cron(-30, 21, -1, -1, -1, target="mule")(add_times)
# 22:00 / 22:30
uwsgidecorators.cron(-30, 22, -1, -1, -1, target="mule")(add_times)
# 23:00 / 23:30
uwsgidecorators.cron(-30, 23, -1, -1, -1, target="mule")(add_times)

