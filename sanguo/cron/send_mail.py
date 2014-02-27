# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/26/14'

import traceback

from django.utils import timezone

from _base import Logger

from apps.server.models import Server as ModelServer
from apps.mail.models import Mail as ModelMail
from core.mail import Mail
from core.activeplayers import ActivePlayers


def send_to_char(char_id, mail):
    m = Mail(char_id)
    m.add(mail.id, mail.name, mail.content, mail.create_at, mail.to_attachment_protobuf().SerializeToString())

def send_one_mail(mail):
    if mail.send_type == 1:
        # 发给某些角色
        char_ids = [int(i) for i in mail.send_to.split(',')]
    elif mail.send_type == 2:
        # 发给指定服务器
        server_ids = [int(i) for i in mail.send_to.split(',')]
        char_ids = []
        for sid in server_ids:
            ap = ActivePlayers(sid)
            char_ids.extend(ap.get_list())
    else:
        # 发送给全部服务器
        server_ids = ModelServer.all_ids()
        char_ids = []
        for sid in server_ids:
            ap = ActivePlayers(sid)
            char_ids.extend(ap.get_list())

    for cid in char_ids:
        send_to_char(cid, mail)


def run():
    mails = ModelMail.objects.filter(send_done=False).filter(send_lock=False).filter(send_at__lte=timezone.now())

    logger = Logger('send_mail.log')
    logger.write("Send Mail Start. mails amount: {0}".format(mails.count()))

    for mail in mails:
        mail.send_lock = True
        mail.save()
        try:
            send_one_mail(mail)
        except Exception as e:
            logger.write("ERROR: mail: {0}, error: {1}".format(mail.id, str(e)))
            logger.write(traceback.format_exc())
        else:
            mail.send_done = True
        finally:
            mail.send_lock = False
            mail.save()

    logger.write("Send Mail Complete")
    logger.close()


if __name__ == '__main__':
    run()

