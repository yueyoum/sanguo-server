# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

from _base import Logger

from django.utils import timezone
from core.mongoscheme import MongoMail
from core.mail import Mail


DAY_DIFF = 3

def clean():
    logger = Logger("clean_mail.log")
    logger.write("Clean Mail Start.")

    now = int(timezone.now().strftime('%s'))
    mails = MongoMail.objects.all()
    amount = 0
    for m in mails:
        char_mail = Mail(m.id)
        for k, v in m.mails.items():
            days, seconds = divmod(now-v.create_at, 3600*24)
            if seconds:
                days += 1
            if days > DAY_DIFF:
                char_mail.delete(k)
                amount += 1

        if len(char_mail.mail.mails) == 0:
            m.delete()

    logger.write("Clean Mail Complete. Cleaned Amount: {0}".format(amount))
    logger.close()


if __name__ == '__main__':
    clean()

