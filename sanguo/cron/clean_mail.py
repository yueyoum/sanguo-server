# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

import traceback

from cron.log import Logger

import uwsgidecorators

from core.mongoscheme import MongoMail
from core.mail import Mail
from preset.settings import MAIL_KEEP_DAYS


# 每天3点清理过期邮件

@uwsgidecorators.cron(0, 3, -1, -1, -1, target="spooler")
def clean(signum):
    logger = Logger("clean_mail.log")
    logger.write("Start")

    try:
        amount = 0

        mails = MongoMail._get_collection().find({}, {'_id': 1})
        for m in mails:
            char_id = m['_id']

            char_mail = Mail(char_id)
            cleaned = char_mail.delete_expired(MAIL_KEEP_DAYS)
            amount += cleaned
    except:
        logger.error(traceback.format_exc())
    else:
        logger.write("Clean Mail Complete. Cleaned Amount: {0}".format(amount))
    finally:
        logger.close()

