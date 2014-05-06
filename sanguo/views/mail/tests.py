# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/2/14'

from django.test import TestCase

from core.mail import Mail
from core.character import char_initialize

from utils import app_test_helper
from libs import crypto
from utils import timezone

import protomsg

class MailTest(TestCase):
    def setUp(self):
        char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))


    def tearDown(self):
        app_test_helper._teardown()


    def _open(self, mail_id, ret=0):
        req = protomsg.OpenMailRequest()
        req.session = self.session
        req.id = mail_id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/mail/open/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == protomsg.RESPONSE_NOTIFY_TYPE["OpenMailResponse"]:
                d = protomsg.OpenMailResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)


    def _delete(self, mail_id, ret=0):
        req = protomsg.DeleteMailRequest()
        req.session = self.session
        req.id = mail_id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/mail/delete/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == protomsg.RESPONSE_NOTIFY_TYPE["DeleteMailResponse"]:
                d = protomsg.DeleteMailResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)


    def _get_attach(self, mail_id, ret=0):
        req = protomsg.GetAttachmentRequest()
        req.session = self.session
        req.id = mail_id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/mail/getattachment/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == protomsg.RESPONSE_NOTIFY_TYPE["GetAttachmentResponse"]:
                d = protomsg.GetAttachmentResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)



    def test_open_mail_normal(self):
        m = Mail(self.char_id)
        mid = m.add('xxx', 'yyy', timezone.utc_timestamp())
        self.assertEqual(m.mail.mails[str(mid)].has_read, False)

        self._open(mid)

        m = Mail(self.char_id)
        self.assertEqual(m.count(), 1)
        self.assertEqual(m.mail.mails[str(mid)].has_read, True)

        app_test_helper._mongo_teardown_func()

    def test_open_mail_error(self):
        self._open(999, 2)


    def test_delete_mail_normal(self):
        mid = Mail(self.char_id).add('xxx', 'yyy', timezone.utc_timestamp())
        self._delete(mid)

        self.assertEqual(Mail(self.char_id).count(), 0)


    def test_delete_mail_error(self):
        self._delete(999, 2)

    #
    # def test_get_attachment(self):
    #     # mid = Mail(self.char_id).add('xxx', 'yyy')
    #     # self._get_attach(mid, 2)
    #     #
    #     # app_test_helper._mongo_teardown_func()
    #     pass
