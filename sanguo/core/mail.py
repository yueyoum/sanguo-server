# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from mongoengine import DoesNotExist
from core.mongoscheme import MongoMail, EmbededMail
from core.msgpipe import publish_to_char
from core.drives import document_ids

from core.exception import InvalidOperate

from preset.settings import MAIL_KEEP_DAYS
from utils import pack_msg
from utils import timezone

import protomsg




class Mail(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mail = MongoMail.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mail = MongoMail(id=self.char_id)
            self.mail.save()


    def count(self):
        return len(self.mail.mails)

    def add(self, name, content, attachment=None):
        """

        @param name: mail name
        @type name: str | unicode
        @param content: mail content
        @type content: str | unicode
        @param attachment: mail attachment
        @type attachment: Drop | None
        @return: new mail id
        @rtype: int
        """

        if not isinstance(name, unicode):
            name = name.decode('utf-8')

        if not isinstance(content, unicode):
            content = content.decode('utf-8')

        mail_id = document_ids.inc('mail')
        m = EmbededMail()
        m.name = name
        m.content = content
        m.attachment = attachment
        m.has_read = False
        m.create_at = timezone.utc_timestamp()

        self.mail.mails[str(mail_id)] = m
        self.mail.save()
        self.send_mail_notify()
        return mail_id

    def delete(self, mail_id):
        """

        @param mail_id: mail id
        @type mail_id: int
        """
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
            raise InvalidOperate()

        self.mail.save()
        self.send_mail_notify()

    def get_attachment(self, mail_id):
        if str(mail_id) not in self.mail.mails:
            raise InvalidOperate()

        if not self.mail.mails[str(mail_id)].attachment:
            raise InvalidOperate()

        # TODO send attachment
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
            m.start_at = v.create_at
            m.max_days = MAIL_KEEP_DAYS

        publish_to_char(self.char_id, pack_msg(msg))