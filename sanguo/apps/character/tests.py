"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from protomsg import (
    RESPONSE_NOTIFY_TYPE,
    CreateCharacterRequest,
    CreateCharacterResponse,
    )

from utils import app_test_helper
from utils import crypto


def teardown():
    app_test_helper._teardown()


class CreateCharacterTest(TestCase):
    def _create(self, account_id, server_id, name, ret):
        session = crypto.encrypt("{0}:{1}".format(account_id, server_id))
        req = CreateCharacterRequest()
        req.session = session
        req.name = name

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/char/create/', data)

        msgs = app_test_helper.unpack_data(res)
        for id_of_msg, len_of_msg, msg in msgs:
            print id_of_msg
            if id_of_msg == RESPONSE_NOTIFY_TYPE["CreateCharacterResponse"]:
                data = CreateCharacterResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def test_normal_create(self):
        self._create(1, 1, "123", 0)

    def test_already_created(self):
        self._create(1, 2, "123", 0)
        self._create(1, 2, "aaa", 200)

    def test_name_has_been_taken(self):
        self._create(2, 2, "xxx", 0)
        self._create(3, 2, "xxx", 201)

    def test_name_too_long(self):
        self._create(4, 2, '1234567890000', 202)


