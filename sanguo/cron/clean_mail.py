# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/27/14'

import datetime
import pytz
from _base import Logger

from django.utils import timezone
from core.mongoscheme import MongoMail
from core.mail import Mail, FORMAT
from preset.settings import MAIL_KEEP_DAYS


def clean():
    logger = Logger("clean_mail.log")
    logger.write("Clean Mail Start.")

    DIFF = timezone.now() - datetime.timedelta(days=MAIL_KEEP_DAYS)
    mails = MongoMail.objects.all()
    amount = 0
    for m in mails:
        char_mail = Mail(m.id, mailobj=m)
        for k, v in m.mails.items():
            create_at = datetime.datetime.strptime(v.create_at, FORMAT)
            create_at = create_at.replace(tzinfo=pytz.utc)
            if create_at < DIFF:
                char_mail.delete(k)
                amount += 1

        if len(char_mail.mail.mails) == 0:
            m.delete()

    logger.write("Clean Mail Complete. Cleaned Amount: {0}".format(amount))
    logger.close()


if __name__ == '__main__':
    clean()

