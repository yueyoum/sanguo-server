# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from mongoengine import DoesNotExist
from core.mongoscheme import MongoMail, MongoEmbededMail
from core.msgpipe import publish_to_char
from core.attachment import Attachment

from core.exception import InvalidOperate

from preset.settings import MAIL_KEEP_DAYS
from utils import pack_msg

import protomsg



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

    def add(self, mail_id, name, content, create_at, attachment=None):
        if not isinstance(name, unicode):
            name = name.decode('utf-8')

        if not isinstance(content, unicode):
            content = content.decode('utf-8')

        m = MongoEmbededMail()
        m.name = name
        m.content = content
        m.attachment = attachment
        m.has_read = False
        m.create_at = create_at

        self.mail.mails[str(mail_id)] = m
        self.mail.save()
        self.send_mail_notify()

    def delete(self, mail_id):

        try:
            self.mail.mails.pop(str(mail_id))
        except KeyError:
            raise InvalidOperate()

        self.mail.save()
        self.send_mail_notify()

    def open(self, mail_id):
        try:
            self.mail.mails[str(mail_id)].has_read = True
        except KeyError:
            raise InvalidOperate("Mail Open. Char {0} Try to open a NONE exist mail {1}".format(self.char_id, mail_id))

        self.mail.save()
        self.send_mail_notify()

    def get_attachment(self, mail_id):
        if str(mail_id) not in self.mail.mails:
            raise InvalidOperate()

        if not self.mail.mails[str(mail_id)].attachment:
            raise InvalidOperate()

        att = Attachment(self.char_id)
        att.send_with_attachment_msg(self.mail.mails[str(mail_id)].attachment)

        self.mail.mails[str(mail_id)].attachment = ''
        self.mail.mails[str(mail_id)].has_read = True
        self.mail.save()
        self.send_mail_notify()


    def send_mail_notify(self):
        msg = protomsg.MailNotify()
        for k, v in self.mail.mails.iteritems():
            m = msg.mails.add()
            m.id = int(k)
            m.name = v.name

            m.content = v.content
            m.has_read = v.has_read
            if v.attachment:
                m.attachment.MergeFromString(v.attachment)
            m.start_at = int(v.create_at.strftime('%s'))
            # m.start_at = v.create_at
            m.max_days = MAIL_KEEP_DAYS

        publish_to_char(self.char_id, pack_msg(msg))