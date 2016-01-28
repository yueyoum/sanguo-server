# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       union_auto_transfer_owner
Date Created:   2016-01-27 11-22
Description:

"""

import json
import traceback

import uwsgidecorators

from cron.log import Logger

from core.union.union import Union

@uwsgidecorators.cron(1, 0, -1, -1, -1, target="spooler")
def clean(signum):
    logger = Logger("union_transfer_owner.log")
    logger.write("Start")

    try:
        result = Union.cronjob_auto_transfer_union()
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Transfer: {0}".format(json.dumps(result)))
    finally:
        logger.close()
