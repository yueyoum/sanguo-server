# -*- coding: utf-8 -*-
from core.character import char_initialize
from django.test import TransactionTestCase
import protomsg
from utils import crypto

from utils import app_test_helper as tests

__author__ = 'Wang Chao'
__date__ = '1/22/14'




class PlunderTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))

        other_char = char_initialize(2, 1, 'b')
        self.other_char_id = other_char.id

    def tearDown(self):
        tests._teardown()

    def test_plunder_list(self):
        req = protomsg.PlunderListRequest()
        req.session = self.session

        data = tests.pack_data(req)
        res = tests.make_request('/plunder/list/', data)
        msgs = tests.unpack_data(res)

    def test_plunder_battle(self):
        req = protomsg.PlunderRequest()
        req.session = self.session
        req.id = self.other_char_id

        data = tests.pack_data(req)
        res = tests.make_request('/plunder/', data)
        msgs = tests.unpack_data(res)
