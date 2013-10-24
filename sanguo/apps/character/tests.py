"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, TransactionTestCase

from protomsg import (
        RESPONSE_NOTIFY_TYPE,
        CommandResponse,
        CreateCharacterRequest,
        CreateCharacterResponse,
        CharacterNotify,
        )

from utils import app_test_helper
from models import Character
from utils import crypto


def teardown():
    from core import redis_client
    redis_client.flushdb()


class CreateCharacterTest(TransactionTestCase):
    fixtures = ['hero.json', ]

    def setUp(self):
        Character.objects.create(
                account_id = 1,
                server_id = 1,
                name = "abcd"
                )

    def _create(self, account_id, server_id, name, ret):
        session = crypto.encrypt("{0}:{1}".format(account_id, server_id))
        req = CreateCharacterRequest()
        req.session = session
        req.name = name

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/char/create/', data)

        msgs = app_test_helper.unpack_data(res)
        if len(msgs) == 1:
            id_of_msg, len_of_msg, msg = msgs[0]
            self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["CommandResponse"])

            data = CommandResponse()
            data.ParseFromString(msg)
            self.assertEqual(data.ret, ret)
            self.assertEqual(data.session, session)
        else:
            for id_of_msg, len_of_msg, msg in msgs:
                self.assertTrue(
                        id_of_msg in [RESPONSE_NOTIFY_TYPE["CharacterNotify"], RESPONSE_NOTIFY_TYPE["HeroNotify"], RESPONSE_NOTIFY_TYPE["CreateCharacterResponse"]]
                        )

    def test_normal_create(self):
        self._create(1, 2, "123", 0)

    def test_already_created(self):
        self._create(1, 1, "123", 200)

    def test_name_has_been_taken(self):
        self._create(2, 1, "abcd", 201)

    def test_invalid_name_length(self):
        self._create(2, 2, "12345678", 202)

