# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

import json

import arrow
from mongoengine import DoesNotExist
from core.mongoscheme import MongoMail, MongoEmbededMail
from core.msgpipe import publish_to_char
from core.attachment import standard_drop_to_attachment_protomsg
from core.resource import Resource
from core.exception import SanguoException
from preset.settings import MAIL_KEEP_DAYS
from utils import pack_msg
import protomsg
from preset import errormsg


class Mail(object):
    def __init__(self, char_id, mailobj=None):
        self.char_id = char_id
        if mailobj:
            self.mail = mailobj
        else:
            try:
                self.mail = MongoMail.objects.get(id=self.char_id)
            except DoesNotExist:
                self.mail = MongoMail(id=self.char_id)
                self.mail.mails = {}
                self.mail.save()

    def count(self):
        return len(self.mail.mails)

    def add(self, name, content, create_at=None, attachment='', send_notify=True):
        if not isinstance(name, unicode):
            name = name.decode('utf-8')

        if not isinstance(content, unicode):
            content = content.decode('utf-8')

        m = MongoEmbededMail()
        m.name = name
        m.content = content
        m.attachment = attachment
        m.has_read = False
        m.create_at = create_at or arrow.utcnow().format('YYYY-MM-DD HH:mm:ss')

        mail_ids = [int(i) for i in self.mail.mails.keys()]
        if not mail_ids:
            mail_id = 1
        else:
            mail_id = max(mail_ids) + 1

        self.mail.mails[str(mail_id)] = m
        self.mail.save()
        if send_notify:
            self.send_notify()
        return mail_id

    def delete(self, mail_id):

        try:
            self.mail.mails.pop(str(mail_id))
        except KeyError:
            raise SanguoException(
                errormsg.MAIL_NOT_EXIST,
                self.char_id,
                "Mail Delete",
                "mail {0} not exist".format(mail_id)
            )

        self.mail.save()
        self.send_notify()

    def open(self, mail_id):
        try:
            self.mail.mails[str(mail_id)].has_read = True
        except KeyError:
            raise SanguoException(
                errormsg.MAIL_NOT_EXIST,
                self.char_id,
                "Mail Open",
                "mail {0} not exist".format(mail_id)
            )

        self.mail.save()
        self.send_notify()

    def get_attachment(self, mail_id):
        if str(mail_id) not in self.mail.mails:
            raise SanguoException(
                errormsg.MAIL_NOT_EXIST,
                self.char_id,
                "Mail Get Attachment",
                "mail {0} not exist".format(mail_id)
            )

        if not self.mail.mails[str(mail_id)].attachment:
            raise SanguoException(
                errormsg.MAIL_HAS_NO_ATTACHMENT,
                self.char_id,
                "Mail Get Attachment",
                "mail {0} has no attachment".format(mail_id)
            )

        resource = Resource(self.char_id, "Mail Attachment")
        attachment = json.loads(self.mail.mails[str(mail_id)].attachment)
        resource.add(**attachment)

        self.mail.mails[str(mail_id)].attachment = ''
        self.mail.mails[str(mail_id)].has_read = True
        self.mail.save()
        self.send_notify()
        return attachment


    def send_notify(self):
        msg = protomsg.MailNotify()
        for k, v in self.mail.mails.iteritems():
            m = msg.mails.add()
            m.id = int(k)
            m.name = v.name

            m.content = v.content
            m.has_read = v.has_read
            if v.attachment:
                m.attachment.MergeFrom(
                    standard_drop_to_attachment_protomsg(json.loads(v.attachment))
                )

            m.start_at = arrow.get(v.create_at, "YYYY-MM-DD HH:mm:ss").timestamp
            m.max_days = MAIL_KEEP_DAYS

        publish_to_char(self.char_id, pack_msg(msg))
