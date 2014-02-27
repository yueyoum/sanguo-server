# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'


import datetime
from django.utils import timezone
from core.mongoscheme import MongoMail
from core.mail import Mail

from _base import Logger

DAY_DIFF = 3

def clean():
    logger = Logger("clean_mail.log")
    logger.write("Clean Mail Start.")

    day = timezone.now() - datetime.timedelta(days=DAY_DIFF)
    mails = MongoMail.objects.all()
    amount = 0
    for m in mails:
        char_mail = Mail(m.id)
        for k, v in m.mails.items():
            if v.create_at < day:
                char_mail.delete(k)
                amount += 1

        if len(char_mail.mail.mails) == 0:
            m.delete()

    logger.write("Clean Mail Complete. Cleaned Amount: {0}".format(amount))
    logger.close()


if __name__ == '__main__':
    clean()

