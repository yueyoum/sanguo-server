# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

from cron.log import Logger
import pytz
import arrow

import uwsgidecorators

from core.mongoscheme import MongoMail
from core.mail import Mail
from preset.settings import MAIL_KEEP_DAYS


# 每天3点清理过期邮件

@uwsgidecorators.cron(0, 3, -1, -1, -1, target="mule")
def clean(signum):
    logger = Logger("clean_mail.log")
    logger.write("Clean Mail Start.")

    DIFF = arrow.utcnow().replace(days=-MAIL_KEEP_DAYS)
    mails = MongoMail.objects.all()
    amount = 0
    for m in mails:
        char_mail = Mail(m.id, mailobj=m)
        for k, v in m.mails.items():
            create_at = arrow.get(v.create_at, 'YYYY-MM-DD HH:mm:ss').replace(tzinfo=pytz.utc)
            if create_at < DIFF:
                char_mail.delete(k)
                amount += 1

        if len(char_mail.mail.mails) == 0:
            m.delete()
        else:
            m.save()

    logger.write("Clean Mail Complete. Cleaned Amount: {0}".format(amount))
    logger.close()

