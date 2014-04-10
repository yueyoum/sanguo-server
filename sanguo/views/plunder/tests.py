# -*- coding: utf-8 -*-
from core.character import char_initialize
from django.test import TestCase
import protomsg
from libs import crypto

from utils import app_test_helper as tests

__author__ = 'Wang Chao'
__date__ = '1/22/14'


class PlunderTest(TestCase):
    def setUp(self):
        char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(1))

        char_initialize(2, 1, 2, 'b')
        self.other_char_id = 2

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
