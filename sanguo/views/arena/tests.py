# -*- coding: utf-8 -*-
from core.character import char_initialize
from django.test import TransactionTestCase
import protomsg
from utils import crypto

from utils import app_test_helper as tests

__author__ = 'Wang Chao'
__date__ = '1/22/14'


class ArenaTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))

        char = char_initialize(2, 1, 'b')
        self.other_char_id = char.id

    def tearDown(self):
        tests._teardown()

    def test_arena_battle(self):
        req = protomsg.ArenaRequest()
        req.session = self.session

        data = tests.pack_data(req)
        res = tests.make_request('/pvp/', data)
        msgs = tests.unpack_data(res)
